from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.i18n import JavaScriptCatalog

from . import views
from .feeds import LatestPostsFeed


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('page/<int:page>', views.post_list, name='posts_list_paged'),
    path('featured/', views.post_list, {'list_type': 'featured'}, name='posts_list_featured'),
    path('featured/<int:page>', views.post_list, {'list_type': 'featured'}, name='posts_list_featured_paged'),

    path('drafts/', views.post_list, {'list_type': 'drafts'}, name='posts_list_drafts'),
    path('drafts/<int:page>', views.post_list, {'list_type': 'drafts'}, name='posts_list_drafts_paged'),

    path('settings/', views.blog_settings, name='settings'),

    path('post/<slug:postURL>', views.post_detail, name='post_detail'),
    path('post/<slug:postURL>/edit', views.post_editor, name='post_edit'),
    path('new/', views.post_editor, name='post_new'),

    path('tags/', views.tags_list, name='tags_list'),
    path('tags/<slug:tag_slug>/', views.post_list, name='tagged_posts'),
    path('tags/<slug:tag_slug>/<int:page>/', views.post_list, name='tagged_posts_paged'),

    path('post/search/<path:query>/', views.post_list, name='search_posts'),

    path('api/posts/edit', views.post_manage, name='post_manage'),
    path('api/posts/publish', views.post_publish, name='post_publish'),
    path('api/posts/<int:postID>/star', views.post_star, name='post_star'),
    path('api/posts/remove', views.post_remove, name='post_remove'),
    path('api/images/file', views.upload_image_file, name='upload_image_file'),
    path('api/images/link', views.upload_image_link, name='upload_image_link'),
    path('api/images/header', views.upload_header_image, name='upload_header_image'),
    path('api/login', views.custom_login, name='login_endpoint'),
    path('api/logout', views.user_logout, name='user_logout'),
    path('api/password_change', views.change_password, name='password_change'),

    path('rss/posts/', LatestPostsFeed(), name='rss_posts'),
    path('jsi18n/', JavaScriptCatalog.as_view(packages=['blog']), name='javascript-catalog'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'blog.views.handler404'
