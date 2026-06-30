import json

from django.contrib.syndication.views import Feed
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils import timezone

from .formatter import RichFormatter
from .models import Post, SiteSettings


class LatestPostsFeed(Feed):
    title = 'Posts from this blog'
    link = '/posts/'
    description = 'All posts from this blog'

    def __init__(self):
        try:
            self.site = SiteSettings.get_solo()
            self.title = f'Posts from {self.site.title}'
        except (OperationalError, ProgrammingError):
            self.site = None

    def items(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        try:
            structure = json.loads(item.content)
        except (TypeError, ValueError):
            return ''

        for block in structure.get('blocks', []):
            if block.get('type') == 'paragraph':
                return RichFormatter._clean_inline((block.get('data') or {}).get('text', ''))
        return ''

    def item_link(self, item):
        return reverse('post_detail', kwargs={'postURL': item.url})
