import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .formatter import RichFormatter
from .models import Post, SiteSettings


class BlogSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(username='author', password='secret-pass')
        self.other_user = User.objects.create_user(username='other', password='secret-pass')
        self.draft = Post.objects.create(
            author=self.author,
            title='Draft',
            url='draft',
            content=json.dumps({'blocks': []}),
            html='',
            published_date=None,
        )

    def test_drafts_are_not_public(self):
        response = self.client.get(reverse('posts_list_drafts'))
        self.assertEqual(response.status_code, 404)

    def test_unpublished_post_is_hidden_from_other_users(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('post_detail', kwargs={'postURL': self.draft.url}))
        self.assertEqual(response.status_code, 404)

    def test_post_manage_rejects_edit_by_non_author(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('post_manage'), {
            'id': self.draft.pk,
            'title': 'Hacked',
            'content': json.dumps({'blocks': []}),
            'tags': '',
        })
        self.assertEqual(response.status_code, 403)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.title, 'Draft')

    def test_star_requires_post(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('post_star', kwargs={'postID': self.draft.pk}))
        self.assertEqual(response.status_code, 405)

    def test_remote_image_upload_rejects_localhost(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('upload_image_link'), {'url': 'http://localhost/image.png'})
        self.assertEqual(response.status_code, 400)


class BlogFunctionalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(username='author', password='secret-pass')

    def test_new_post_can_be_saved(self):
        self.client.force_login(self.author)
        content = json.dumps({'blocks': [{'type': 'paragraph', 'data': {'text': 'Hello'}}]})
        response = self.client.post(reverse('post_manage'), {
            'title': 'Hello World',
            'content': content,
            'tags': 'test',
        })
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(title='Hello World')
        self.assertEqual(post.url, 'hello-world')
        self.assertIn('<p class="post-entry">Hello</p>', post.html)

    def test_slug_does_not_change_when_existing_post_is_saved(self):
        post = Post.objects.create(
            author=self.author,
            title='Stable Title',
            url='stable-title',
            content=json.dumps({'blocks': []}),
            html='',
        )
        post.process().save()
        post.refresh_from_db()
        self.assertEqual(post.url, 'stable-title')


    def test_default_avatar_uses_static_asset(self):
        site = SiteSettings.get_solo()
        site.avatar = ''
        site.save(update_fields=['avatar'])
        self.assertEqual(site.avatar_url, '/static/images/no-avatar.png')

        site.avatar = 'no-avatar.png'
        site.save(update_fields=['avatar'])
        self.assertEqual(site.avatar_url, '/static/images/no-avatar.png')

    def test_formatter_strips_unsafe_html(self):
        content = json.dumps({
            'blocks': [
                {'type': 'paragraph', 'data': {'text': '<script>alert(1)</script><b>safe</b>'}},
                {'type': 'image', 'data': {'file': {'url': 'https://evil.example/x.png'}, 'caption': 'x'}},
            ]
        })
        html = RichFormatter(content).toHTML()
        self.assertNotIn('<script>', html)
        self.assertNotIn('evil.example', html)
        self.assertIn('<b>safe</b>', html)
