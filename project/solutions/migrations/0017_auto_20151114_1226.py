# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20151023_1959'),
        ('solutions', '0016_auto_20151114_1216'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcaseresult',
            name='test_case',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='problems.TestCase', null=True),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='memory_limit',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='time_limit',
            field=models.IntegerField(default=0),
        ),
    ]
