# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0007_auto_20160126_1912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='attachment',
            field=models.ForeignKey(to='storage.FileMetadata'),
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='attachment',
            field=models.ForeignKey(to='storage.FileMetadata'),
        ),
    ]
