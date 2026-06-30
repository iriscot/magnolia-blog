import ipaddress
import operator
import socket
import uuid
from functools import reduce
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps, UnidentifiedImageError
from taggit.models import Tag

from .forms import PostEditorForm, SiteSettingsForm, UploadHeaderImageForm
from .models import Post, SiteSettings


ALLOWED_IMAGE_FORMATS = {
    'JPEG': 'jpg',
    'PNG': 'png',
    'GIF': 'gif',
    'WEBP': 'webp',
}
PRIVATE_HOSTS = {'localhost'}


def post_list(request, page=1, query=None, list_type=None, tag_slug=None):
    site = SiteSettings.get_solo()
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    page_title = site.title
    paged_url = 'posts_list_paged'

    if query:
        clean_query = query.strip()
        if clean_query:
            page_title = _('Searching «%s»') % clean_query
            query_list = clean_query.split()
            title_query = reduce(operator.and_, (Q(title__icontains=q) for q in query_list))
            html_query = reduce(operator.and_, (Q(html__icontains=q) for q in query_list))
            posts = posts.filter(title_query | html_query)

    if list_type == 'featured':
        posts = posts.filter(is_starred=True)
        page_title = _('Featured posts')
        paged_url = 'posts_list_featured_paged'

    if list_type == 'drafts':
        if not request.user.is_authenticated:
            raise Http404
        posts = Post.objects.filter(author=request.user, published_date__isnull=True).order_by('-created_date')
        page_title = _('Drafts')
        paged_url = 'posts_list_drafts_paged'

    if tag_slug:
        rq_tag = get_object_or_404(Tag, slug=tag_slug)
        posts = Post.objects.filter(
            tags__slug=tag_slug,
            published_date__lte=timezone.now(),
        ).order_by('-published_date')
        page_title = _('Tagged «%s»') % rq_tag.name
        paged_url = 'tagged_posts_paged'

    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    try:
        current_page = paginator.page(page)
    except EmptyPage:
        raise Http404

    return render(
        request,
        'blog/post_list.html',
        {
            'title': page_title,
            'page': current_page,
            'url_paged': paged_url,
            'tag': tag_slug,
        },
    )


def post_detail(request, postURL):
    post = get_object_or_404(Post, url=postURL)
    if post.published_date is None and (not request.user.is_authenticated or post.author != request.user):
        raise Http404
    return render(request, 'blog/show_post.html', {'post': post})


def tags_list(request):
    tags_with_post_count = Tag.objects.annotate(num_posts=Count('taggit_taggeditem_items'))
    ordered_tags = tags_with_post_count.exclude(num_posts=0).order_by('-num_posts')
    return render(request, 'blog/tags.html', {'tags': ordered_tags})


@login_required(login_url='/admin/')
def post_editor(request, postURL=None):
    if postURL:
        post = get_object_or_404(Post, url=postURL)
        if post.author != request.user:
            return HttpResponseForbidden()
        return render(request, 'blog/editor.html', {'post': post, 'tags': post.tags.all(), 'title': post.title})
    return render(request, 'blog/editor.html', {'title': _('New post')})


@login_required(login_url='/admin/')
@require_POST
def post_manage(request):
    title = request.POST.get('title', _('No title')).strip() or _('No title')

    if request.POST.get('id'):
        post = get_object_or_404(Post, pk=request.POST.get('id'))
        if post.author != request.user:
            return HttpResponseForbidden()
    else:
        post = Post(author=request.user, title=title, url='', content='', html='')

    form = PostEditorForm(request.POST, instance=post)
    if not form.is_valid():
        return HttpResponseBadRequest('content malformed')

    post = form.save(commit=False)
    post.title = title
    post.content = request.POST.get('content', '')
    post.modified_date = timezone.now()
    post.process().save()
    form.save_m2m()

    return JsonResponse({'url': reverse('post_detail', args=[post.url])})


@login_required(login_url='/admin/')
@require_POST
def post_publish(request):
    post = get_object_or_404(Post, pk=request.POST.get('id'))
    if post.author != request.user:
        return HttpResponseForbidden()
    post.publish()
    return redirect('post_detail', postURL=post.url)


@login_required(login_url='/admin/')
@require_POST
def post_remove(request):
    post = get_object_or_404(Post, pk=request.POST.get('id'))
    if post.author != request.user:
        return HttpResponseForbidden()
    post.delete()
    return JsonResponse({'success': True})


@login_required(login_url='/admin/')
@require_POST
def post_star(request, postID):
    post = get_object_or_404(Post, pk=postID)
    if post.author != request.user:
        return HttpResponseForbidden()
    post.toggleStar()
    return redirect('post_detail', postURL=post.url)


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'message': str(message)}, status=status)


def _validate_image_file(file_obj, max_size):
    if getattr(file_obj, 'size', None) and file_obj.size > max_size:
        raise ValidationError(_('Image is too large.'))

    try:
        file_obj.seek(0)
        image = Image.open(file_obj)
        image.verify()
        image_format = image.format
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError(_('Uploaded file is not a valid image.')) from exc
    finally:
        try:
            file_obj.seek(0)
        except (AttributeError, OSError):
            pass

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(_('This image format is not allowed.'))
    return ALLOWED_IMAGE_FORMATS[image_format]


def _optimize_image(file_path):
    try:
        with Image.open(file_path) as image:
            image = ImageOps.exif_transpose(image)
            save_kwargs = {'optimize': True}
            if image.format in {'JPEG', 'WEBP'}:
                save_kwargs['quality'] = 85
            image.save(file_path, **save_kwargs)
    except (OSError, ValueError):
        return


@login_required(login_url='/admin/')
@require_POST
def upload_image_file(request):
    uploaded_file = request.FILES.get('image')
    if not uploaded_file:
        return _json_error(_('No image was uploaded.'))
    try:
        return _upload_image(uploaded_file, settings.MAX_UPLOAD_SIZE)
    except ValidationError as exc:
        return _json_error(exc.messages[0] if exc.messages else exc)


@login_required(login_url='/admin/')
@require_POST
def upload_image_link(request):
    url = request.POST.get('url', '').strip()
    if not url:
        return _json_error(_('No image URL was provided.'))
    try:
        remote_file = _download_remote_image(url)
        return _upload_image(remote_file, settings.MAX_REMOTE_IMAGE_SIZE)
    except (ValidationError, requests.RequestException) as exc:
        return _json_error(exc)


def _upload_image(file_obj, max_size):
    extension = _validate_image_file(file_obj, max_size)
    unique_filename = f'{uuid.uuid4()}.{extension}'

    fs = FileSystemStorage()
    name = fs.save(unique_filename, file_obj)
    _optimize_image(fs.path(name))
    return JsonResponse({'success': True, 'file': {'url': fs.url(name)}})


def _download_remote_image(url):
    current_url = url
    for _ in range(3):
        _validate_public_url(current_url)
        response = requests.get(
            current_url,
            stream=True,
            timeout=settings.REMOTE_IMAGE_TIMEOUT,
            allow_redirects=False,
            headers={'User-Agent': 'MagnoliaBlog/1.0'},
        )
        if response.is_redirect:
            location = response.headers.get('Location')
            if not location:
                raise ValidationError(_('Remote image redirect is invalid.'))
            current_url = urljoin(current_url, location)
            continue

        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise ValidationError(_('Remote URL does not point to an image.'))

        buffer = BytesIO()
        total_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            total_size += len(chunk)
            if total_size > settings.MAX_REMOTE_IMAGE_SIZE:
                raise ValidationError(_('Remote image is too large.'))
            buffer.write(chunk)

        buffer.seek(0)
        filename = Path(urlparse(current_url).path).name or 'remote-image'
        return ContentFile(buffer.getvalue(), name=filename)

    raise ValidationError(_('Remote image has too many redirects.'))


def _validate_public_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValidationError(_('Only HTTP(S) image URLs are allowed.'))
    hostname = parsed.hostname.strip().lower()
    if hostname in PRIVATE_HOSTS:
        raise ValidationError(_('Private hosts are not allowed.'))

    try:
        addresses = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValidationError(_('Image host could not be resolved.')) from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if any([
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]):
            raise ValidationError(_('Private network URLs are not allowed.'))


@login_required(login_url='/admin/')
@require_POST
def upload_header_image(request):
    form = UploadHeaderImageForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseForbidden('this file type is not allowed')

    uploaded_file = request.FILES['image']
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        return _json_error(_('Image is too large.'))

    site = SiteSettings.get_solo()
    site.delete_avatar()
    site.avatar = uploaded_file
    site.save()
    url = site.crop_avatar()
    return JsonResponse({'success': True, 'url': url})


@login_required(login_url='/admin/')
def blog_settings(request):
    password_form = PasswordChangeForm(request.user)
    site = SiteSettings.get_solo()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            return render(
                request,
                'blog/site_settings.html',
                {'form': form, 'is_saved': True, 'password_form': password_form},
            )
    else:
        form = SiteSettingsForm(instance=site)
    return render(request, 'blog/site_settings.html', {'form': form, 'password_form': password_form})


@require_POST
def custom_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid username or password.'}, status=401)


@login_required(login_url='/admin/')
@require_POST
def user_logout(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/admin/')
@require_POST
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)


def handler404(request, exception):
    return render(request, 'blog/errors/404.html', status=404)
