from django.utils import timezone
from .models import Post, SiteSettings
from django.shortcuts import render, get_object_or_404, redirect
from .forms import SiteSettingsForm, UploadHeaderImageForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseNotFound, Http404, HttpResponse, JsonResponse
from tagging.models import Tag, TaggedItem
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage
from django.core.files import File
from django.db.models import Q
from django.utils.html import escape
import urllib
import os
import operator
import time
from functools import reduce
from django.utils.translation import ugettext_lazy as _



def post_list(request, page=1, query=False, type=False, tag=False):
    site = SiteSettings.get_solo()
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    page_title = site.title
    paged_url = 'posts_list_paged'
    tag_name = ''

    if query:
        page_title = _('Searching %s') % '&laquo;'+escape(query)+'&raquo;'
        query_list = query.split()
        posts = posts.filter(
            reduce(operator.and_,
                    (Q(title__contains=q) for q in query_list)) |
            reduce(operator.and_,
                   (Q(html__contains=q) for q in query_list))
        )

    if(type == 'featured'):
        posts = posts.filter(is_starred=True)
        page_title = _('Featured posts')
        paged_url = 'posts_list_featured_paged'

    if (type == 'drafts'):
        posts = Post.objects.filter(published_date=None).order_by('-created_date')
        page_title = _('Drafts')
        paged_url = 'posts_list_drafts_paged'

    if(tag):
        rq_tag = Tag.objects.get(name=tag)
        posts = TaggedItem.objects.get_by_model(Post, rq_tag).filter(published_date__lte=timezone.now()).order_by('-published_date')
        page_title = _('Tagged %s') % '&laquo;'+rq_tag.name+'&raquo;'
        paged_url = 'tagged_posts_paged'
        tag_name = rq_tag.name

    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    try:
        current_page = paginator.page(page)
    except EmptyPage:
        raise Http404
    return render(request, 'blog/post_list.html', {'title': page_title, 'page': current_page, 'url_paged': paged_url, 'tag': tag_name})

def post_detail(request, postURL):
    post = get_object_or_404(Post, url=postURL)
    if post.published_date == None and not request.user.is_authenticated:
        raise Http404
    return render(request, 'blog/show_post.html', {'post': post})

def tags_list(request):
    return render(request, 'blog/tags.html')


@login_required(login_url='/admin/')
def post_editor(request, postURL=None):
    if(postURL):
        post = get_object_or_404(Post, url=postURL)
        return render(request, 'blog/editor.html', {'post': post, 'tags': post.getTags(True), 'title': post.title})
    else:
        return render(request, 'blog/editor.html', {'title': 'New post'})


@login_required(login_url='/admin/')
def post_manage(request):
    if request.method == "POST":

        if request.POST.get('id', False): # Post exists, edit it! 
            post = get_object_or_404(Post, pk=request.POST.get('id'))
            post.content = request.POST.get('content', '')
            post.title = request.POST.get('title', _('No title'))
            post.modified_date = timezone.now()
            post.process().tag(request.POST.get('tags')).save();
            return JsonResponse({'url': reverse('post_detail', args=[post.url])})

        else:  # Create a new post
            newPost = Post.objects.create(author=request.user, title=request.POST.get('title', _('No title')), content=request.POST.get('content', ''))
            newPost.modified_date = timezone.now()
            newPost.process().tag(request.POST.get('tags')).save()
            return JsonResponse({'url': reverse('post_detail', args=[newPost.url])})


@login_required(login_url='/admin/')
def post_publish(request):
    if request.method == "POST":
        post = get_object_or_404(Post, pk=request.POST.get('id'))
        if post.author != request.user:
            return HttpResponseForbidden() 
        post.publish();
        return redirect('post_detail', postURL=post.url)


@login_required(login_url='/admin/')
def post_remove(request, postID):
    if request.method == "GET":
        post = get_object_or_404(Post, pk=postID)
        if post.author != request.user:
            return HttpResponseForbidden() 
        post.delete();
        return redirect('post_list')

@login_required(login_url='/admin/')
def post_star(request, postID):
    if request.method == "GET":
        post = get_object_or_404(Post, pk=postID)
        if post.author != request.user:
            return HttpResponseForbidden() 
        post.toggleStar();
        return redirect('post_detail', postURL=post.url)


@login_required(login_url='/admin/')
def upload_image_file(request):
    uploaded_file = request.FILES['image']
    fs = FileSystemStorage()
    name = fs.save(uploaded_file.name, uploaded_file)
    return JsonResponse({
        'success': 1,
        'file': {
            'url': fs.url(name)
        }})


@login_required(login_url='/admin/')
def upload_image_link(request):
    image = urllib.request.urlretrieve(request.POST.get('url'))
    fs = FileSystemStorage()
    image_file = File(open(image[0], 'rb'))
    name = fs.save(str(int(time.time()))+'.jpg', image_file)
    return JsonResponse({
        'success': 1,
        'file': {
            'url': fs.url(name)
        }})


@login_required(login_url='/admin/')
def upload_header_image(request):
    if request.method == 'POST':
        form = UploadHeaderImageForm(request.POST, request.FILES)
        if form.is_valid():
            site = SiteSettings.get_solo()
            if request.POST.get('image_type') == 'cover':
                # handle cover
                site.cover = request.FILES['image']
                site.save()
            elif request.POST.get('image_type') == 'avatar':
                # handle avatar
                site.avatar = request.FILES['image']
                site.save()
                site.crop_avatar()
            else:
                return HttpResponseForbidden('method not allowed')
            return JsonResponse({'success': 1})
        else:
            return HttpResponseForbidden('this file type is not allowed')
    return HttpResponseForbidden('allowed only via POST')


@login_required(login_url='/admin/')
def blog_settings(request):
    site = SiteSettings.get_solo()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            return render(request, 'blog/site_settings.html', {'form': form, 'is_saved': True})
    else:
        form = SiteSettingsForm(instance=site)
        return render(request, 'blog/site_settings.html', {'form': form})


def handler404(request, exception):
    context = RequestContext(request)
    response = render(request, "blog/errors/404.html", context=context)
    response.status_code = 404
    return response