from django import forms

from .models import Post
from .models import SiteSettings

from django.utils.translation import ugettext_lazy as _



class SiteSettingsForm(forms.ModelForm):


	class Meta:
		model = SiteSettings
		fields = ('title', 'description', 'author', 'social_instagram', 'social_twitter', 'social_facebook', 'social_youtube', 'social_vk', 'social_telegram', 'social_email')


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


class UploadHeaderImageForm(forms.Form):
      image = forms.ImageField()
      image_type = forms.CharField(max_length=10)