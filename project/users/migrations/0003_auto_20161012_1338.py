# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20160705_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='kind',
            field=models.IntegerField(default=1, verbose_name='kind', choices=[(1, 'Person'), (2, 'Team')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='members',
            field=models.CharField(max_length=255, verbose_name='members', blank=True),
        ),
    ]
