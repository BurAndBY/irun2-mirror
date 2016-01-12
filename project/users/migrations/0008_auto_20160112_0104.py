# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_userprofile_last_used_compiler'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='has_api_access',
            field=models.BooleanField(default=False, verbose_name='API access'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='needs_change_password',
            field=models.BooleanField(default=False, verbose_name='password needs to be changed by user'),
        ),
    ]
