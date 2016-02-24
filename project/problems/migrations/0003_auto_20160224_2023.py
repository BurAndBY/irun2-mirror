# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_auto_20160206_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='description',
            field=models.TextField(verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='description',
            field=models.TextField(verbose_name='description', blank=True),
        ),
    ]
