# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0010_auto_20160126_1938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
