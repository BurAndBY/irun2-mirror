# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_testcase_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='answer_size',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='input_size',
            field=models.IntegerField(default=0),
        ),
    ]
