# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='photo',
            field=storage.storage.ResourceIdField(null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='photo_thumbnail',
            field=storage.storage.ResourceIdField(null=True),
        ),
    ]
