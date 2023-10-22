from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Post, SiteSettings
import json
from collections import namedtuple
from django.db.utils import OperationalError


class LatestPostsFeed(Feed):
    title = "Posts from this blog"
    link = "/posts/"
    description = "All posts from this blog"

    def __init__(self):
        try:
            self.site = SiteSettings.get_solo()
            self.title = "Posts from "+self.site.title
        except OperationalError:
            return None

    def items(self):
        return Post.objects.all().order_by("-published_date")[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        description = ''
        # try to generate desc from first paragraph
        structure = json.loads(
            item.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        for block in structure.blocks:
            if block.type == 'paragraph':
                description = block.data.text
        return description

    def item_link(self, item):
        return reverse('post_detail', kwargs={'postURL': item.url})
