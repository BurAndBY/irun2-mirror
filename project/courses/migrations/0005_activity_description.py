# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_activityrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='description',
            field=models.TextField(max_length=255, verbose_name='description', blank=True),
        ),
    ]
