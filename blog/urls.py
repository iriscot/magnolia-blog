from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .feeds import LatestPostsFeed
from django.views.i18n import JavaScriptCatalog


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('page/<int:page>', views.post_list, name='posts_list_paged'),
    path('featured/', views.post_list,
         {'type': 'featured'}, name='posts_list_featured'),
    path('featured/<int:page>', views.post_list,
         {'type': 'featured'}, name='posts_list_featured_paged'),

    path('drafts/', views.post_list,
         {'type': 'drafts'}, name='posts_list_drafts'),
    path('drafts/<int:page>', views.post_list,
         {'type': 'drafts'}, name='posts_list_drafts_paged'),

    path('settings/', views.blog_settings, name='settings'),

    path('post/<slug:postURL>', views.post_detail, name='post_detail'),

    path('post/<slug:postURL>/edit', views.post_editor, name='post_edit'),
    path('new/', views.post_editor, name='post_new'),

    path(r'tags/', views.tags_list, name='tags_list'),

    re_path(r'^tags/(?P<tag_slug>[^\d/][\w-]+)/$',
            views.post_list, name='tagged_posts'),
    re_path(r'^tags/(?P<tag_slug>[^\d/][\w-]+)/(?P<page>\d+)/$',
            views.post_list, name='tagged_posts_paged'),

    re_path(r'^posts/search/(?P<query>[\w]+)/$',
            views.post_list, name='search_posts'),

    path('api/posts/edit', views.post_manage, name='post_manage'),
    path('api/posts/publish', views.post_publish, name='post_publish'),
    path('api/posts/<int:postID>/star', views.post_star, name='post_star'),
    path('api/posts/<int:postID>/remove',
         views.post_remove, name='post_remove'),
    path('api/images/file', views.upload_image_file, name='upload_image_file'),
    path('api/images/link', views.upload_image_link, name='upload_image_link'),
    path('api/images/header', views.upload_header_image,
         name='upload_header_image'),

    path('rss/posts/', LatestPostsFeed(), name='rss_posts'),

    path('jsi18n/',
         JavaScriptCatalog.as_view(packages=['blog']), name='javascript-catalog'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'blog.views.handler404'
