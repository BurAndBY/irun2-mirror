# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20161012_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='can_change_name',
            field=models.BooleanField(default=False, verbose_name='user is allowed to change name'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_change_password',
            field=models.BooleanField(default=True, verbose_name='user is allowed to change password'),
        ),
    ]
