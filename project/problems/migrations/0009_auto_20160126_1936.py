# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0008_auto_20160126_1913'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problemrelatedfile',
            name='attachment',
        ),
        migrations.RemoveField(
            model_name='problemrelatedsourcefile',
            name='attachment',
        ),
        migrations.AddField(
            model_name='problemrelatedfile',
            name='filename',
            field=models.CharField(default='a', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemrelatedfile',
            name='resource_id',
            field=storage.storage.ResourceIdField(default='a'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemrelatedfile',
            name='size',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemrelatedsourcefile',
            name='filename',
            field=models.CharField(default='b', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemrelatedsourcefile',
            name='resource_id',
            field=storage.storage.ResourceIdField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemrelatedsourcefile',
            name='size',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
