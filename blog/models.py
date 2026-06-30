import json
import os
import posixpath
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.templatetags.static import static
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps
from pytils import translit
from solo.models import SingletonModel
from taggit.managers import TaggableManager

from .formatter import RichFormatter


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    html = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    modified_date = models.DateTimeField(default=timezone.now)
    is_starred = models.BooleanField(default=False)
    tags = TaggableManager(blank=True)

    @staticmethod
    def getOrNone(**kwargs):  # noqa: N802 - keep backwards-compatible API
        try:
            return Post.objects.get(**kwargs)
        except Post.DoesNotExist:
            return None

    def process(self):
        base_url = translit.slugify(self.title) or uuid.uuid4().hex[:12]
        unique_url = base_url[:200]

        counter = 1
        queryset = Post.objects.filter(url=unique_url)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        while queryset.exists():
            suffix = f'-{counter}'
            unique_url = f'{base_url[:200 - len(suffix)]}{suffix}'
            queryset = Post.objects.filter(url=unique_url)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            counter += 1

        self.url = unique_url
        self.html = RichFormatter(self.content).toHTML()
        return self

    def publish(self):
        self.published_date = timezone.now()
        self.save(update_fields=['published_date'])

    def toggleStar(self):  # noqa: N802 - keep backwards-compatible API
        self.is_starred = not self.is_starred
        self.save(update_fields=['is_starred'])

    def delete(self, *args, **kwargs):
        self._delete_embedded_images()
        super().delete(*args, **kwargs)

    def _delete_embedded_images(self):
        try:
            content_data = json.loads(self.content)
        except (TypeError, ValueError):
            return

        for block in content_data.get('blocks', []):
            if block.get('type') != 'image':
                continue
            image_url = (block.get('data') or {}).get('file', {}).get('url')
            storage_name = self._storage_name_from_media_url(image_url)
            if storage_name and default_storage.exists(storage_name):
                default_storage.delete(storage_name)

    @staticmethod
    def _storage_name_from_media_url(image_url):
        if not image_url:
            return None
        path = urlparse(str(image_url)).path
        if not path.startswith(settings.MEDIA_URL):
            return None
        storage_name = path[len(settings.MEDIA_URL):].lstrip('/')
        normalized = posixpath.normpath(storage_name)
        if normalized.startswith('../') or normalized == '..':
            return None
        return normalized

    def __str__(self):
        return self.title


@receiver(pre_delete, sender=Post)
def remove_tags_when_last_post_deleted(sender, instance, **kwargs):
    for tag in instance.tags.all():
        if tag.taggit_taggeditem_items.count() == 1:
            tag.delete()


@deconstructible
class UniqueFilename:
    def __call__(self, instance, filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
        return f'{uuid.uuid4()}.{ext}'


DEFAULT_AVATAR_NAMES = {'', 'no-avatar.png', 'meta/no-avatar.png'}


class SiteSettings(SingletonModel):
    title = models.CharField(max_length=256, default=_('My new blog'))
    description = models.CharField(max_length=256, blank=True)
    author = models.CharField(max_length=256, default=_('Me'))

    avatar = models.ImageField(upload_to=UniqueFilename(), blank=True)

    @property
    def avatar_url(self):
        """Return an uploaded avatar URL or the static fallback.

        Media is for user uploads and is intentionally ignored by Git.  The
        built-in fallback avatar is a static asset and must not live under
        MEDIA_ROOT.
        """
        name = (self.avatar.name or '').strip()
        if name in DEFAULT_AVATAR_NAMES:
            return static('images/no-avatar.png')

        try:
            return self.avatar.url
        except ValueError:
            return static('images/no-avatar.png')

    social_instagram = models.CharField(max_length=256, blank=True)
    social_twitter = models.CharField(max_length=256, blank=True)
    social_facebook = models.CharField(max_length=256, blank=True)
    social_youtube = models.CharField(max_length=256, blank=True)
    social_vk = models.CharField(max_length=256, blank=True)
    social_telegram = models.CharField(max_length=256, blank=True)
    social_email = models.EmailField(max_length=256, blank=True)

    def crop_avatar(self):
        old_name = self.avatar.name or ''
        image = Image.open(self.avatar)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((300, 300))

        width, height = image.size
        crop_size = min(width, height)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        image = image.crop((left, top, left + crop_size, top + crop_size))

        new_name = f'{uuid.uuid4()}.webp'
        new_path = default_storage.path(new_name)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        image.save(new_path, 'WEBP', quality=85)

        if old_name not in DEFAULT_AVATAR_NAMES and old_name != new_name and default_storage.exists(old_name):
            default_storage.delete(old_name)

        self.avatar.name = new_name
        self.save(update_fields=['avatar'])
        return self.avatar.url

    def delete_avatar(self):
        name = self.avatar.name or ''
        if name not in DEFAULT_AVATAR_NAMES and default_storage.exists(name):
            default_storage.delete(name)

    def __str__(self):
        return _('Site configuration')
