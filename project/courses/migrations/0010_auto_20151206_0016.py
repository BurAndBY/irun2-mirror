# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_auto_20151205_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='bonus_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='assignment',
            name='extra_requirements',
            field=models.TextField(max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='extra_requirements_ok',
            field=models.BooleanField(default=False),
        ),
    ]
