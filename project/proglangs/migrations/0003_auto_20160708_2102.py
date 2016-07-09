# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0002_compilerdetails'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compiler',
            name='legacy',
        ),
        migrations.AddField(
            model_name='compiler',
            name='default_for_contests',
            field=models.BooleanField(default=False, verbose_name='compiler is enabled by default in new contests'),
        ),
        migrations.AddField(
            model_name='compiler',
            name='default_for_courses',
            field=models.BooleanField(default=False, verbose_name='compiler is enabled by default in new courses'),
        ),
    ]
