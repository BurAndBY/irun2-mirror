# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0004_auto_20151115_1205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='memory_limit',
            field=models.IntegerField(default=0),
        ),
    ]
