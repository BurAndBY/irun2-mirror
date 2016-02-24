# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0004_auto_20160225_0215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='difficulty',
            field=models.IntegerField(default=None, null=True, verbose_name='difficulty', blank=True),
        ),
    ]
