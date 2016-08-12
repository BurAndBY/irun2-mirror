# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0011_auto_20160514_1942'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemextrainfo',
            name='sample_test_count',
            field=models.IntegerField(default=0, verbose_name='number of sample tests'),
        ),
    ]
