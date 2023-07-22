# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.resource_id


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='photo',
            field=storage.resource_id.ResourceIdFieldDeprecated(null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='photo_thumbnail',
            field=storage.resource_id.ResourceIdFieldDeprecated(null=True),
        ),
    ]
