from django import forms

from .models import SiteSettings, Post
from taggit.forms import TagField
from django.utils.translation import gettext_lazy as _


class SiteSettingsForm(forms.ModelForm):

    class Meta:
        model = SiteSettings
        fields = ('title', 'description', 'author', 'social_instagram', 'social_twitter',
                  'social_facebook', 'social_youtube', 'social_vk', 'social_telegram', 'social_email')

        labels = {
            "title": _("Blog title"),
            "description": _("Blog description"),
            "author": _("Blog author"),

            "social_instagram": _("Instagram username"),
            "social_twitter": _("Twitter username"),
            "social_facebook": _("Facebook username"),
            "social_youtube": _("YouTube username"),
            "social_vk": _("VK username"),
            "social_telegram": _("Telegram username"),
            "social_email": _("E-Mail"),
        }

        title = forms.CharField(required=True)
        author = forms.CharField(required=True)


class UploadHeaderImageForm(forms.Form):
    image = forms.ImageField()


class PostEditorForm(forms.ModelForm):
    tags = TagField(required=False)

    class Meta:
        model = Post
        fields = ('title', 'content', 'tags')
