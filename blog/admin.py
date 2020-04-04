from django.contrib import admin
from .models import Post
from solo.admin import SingletonModelAdmin
from .models import SiteSettings



admin.site.register(Post)



admin.site.register(SiteSettings, SingletonModelAdmin)
