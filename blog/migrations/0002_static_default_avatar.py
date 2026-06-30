# Generated for media/static separation.

import blog.models
from django.db import migrations, models


def move_default_avatar_out_of_media(apps, schema_editor):
    SiteSettings = apps.get_model('blog', 'SiteSettings')
    SiteSettings.objects.filter(avatar__in=['no-avatar.png', 'meta/no-avatar.png']).update(avatar='')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(move_default_avatar_out_of_media, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sitesettings',
            name='avatar',
            field=models.ImageField(blank=True, upload_to=blog.models.UniqueFilename()),
        ),
    ]
