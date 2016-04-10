# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0008_auto_20160325_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemfolder',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
    ]
