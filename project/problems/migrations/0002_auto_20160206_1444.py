# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='description',
            field=models.TextField(verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='ordinal_number',
            field=models.PositiveIntegerField(default=0, verbose_name='number'),
        ),
    ]
