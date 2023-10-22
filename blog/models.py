from django.conf import settings
from django.db import models
from django.utils import timezone
from .formatter import RichFormatter
from pytils import translit
from taggit.managers import TaggableManager
from solo.models import SingletonModel
from PIL import Image
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import pre_delete
import time


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    content = models.TextField()
    html = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    modified_date = models.DateTimeField(default=timezone.now)
    is_starred = models.BooleanField(default=False)
    tags = TaggableManager()

    def getOrNone(**kwargs):
        try:
            return Post.objects.get(**kwargs)
        except Post.DoesNotExist:
            return None

    def process(self):
        if(not self.published_date):
            self.url = translit.slugify(self.title)

        # Avoid dupes

        while Post.getOrNone(url=self.url):
            self.url = str(int(time.time())+1)+'-'+translit.slugify(self.title)

        formatter = RichFormatter(self.content)
        self.html = formatter.toHTML()
        return self

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def toggleStar(self):
        self.is_starred = not self.is_starred
        self.save()


@receiver(pre_delete, sender=Post)
def remove_tags_when_last_post_deleted(sender, instance, **kwargs):
    for tag in instance.tags.all():
        # Check if the tag is associated with only this post
        if tag.taggit_taggeditem_items.count() == 1:
            # If it's the last post with this tag, delete the tag
            tag.delete()


def __str__(self):
    return self.title


class SiteSettings(SingletonModel):
    title = models.CharField(max_length=256, default=_("My new blog"))
    description = models.CharField(max_length=256, blank=True)
    author = models.CharField(max_length=256, default=_("Me"))

    avatar = models.ImageField(upload_to='meta/', default='meta/no-avatar.png')

    social_instagram = models.CharField(max_length=256, blank=True)
    social_twitter = models.CharField(max_length=256, blank=True)
    social_facebook = models.CharField(max_length=256, blank=True)
    social_youtube = models.CharField(max_length=256, blank=True)
    social_vk = models.CharField(max_length=256, blank=True)
    social_telegram = models.CharField(max_length=256, blank=True)
    social_email = models.CharField(max_length=256, blank=True)

    def crop_avatar(self):
        img = Image.open(self.avatar.path)
        width, height = img.size  # Get dimensions

        if width > 300 and height > 300:
            # keep ratio but shrink down
            img.thumbnail((width, height))

        # check which one is smaller
        if height < width:
            # make square by cutting off equal amounts left and right
            left = (width - height) / 2
            right = (width + height) / 2
            top = 0
            bottom = height
            img = img.crop((left, top, right, bottom))

        elif width < height:
            # make square by cutting off bottom
            left = 0
            right = width
            top = 0
            bottom = width
            img = img.crop((left, top, right, bottom))

        if width > 300 and height > 300:
            img.thumbnail((300, 300))

        img.save(self.avatar.path)

    def __str__(self):
        return _('Site configuration')
