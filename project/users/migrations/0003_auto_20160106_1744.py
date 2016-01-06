# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20160105_0119'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='needs_change_password',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='patronymic',
            field=models.CharField(max_length=30, verbose_name='patronymic', blank=True),
        ),
    ]
