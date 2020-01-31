# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0009_auto_20160407_0148'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemextrainfo',
            name='default_memory_limit',
            field=models.IntegerField(default=1073741824),
        ),
        migrations.AddField(
            model_name='problemextrainfo',
            name='default_time_limit',
            field=models.IntegerField(default=1000),
        ),
        migrations.AlterField(
            model_name='problemextrainfo',
            name='problem',
            field=models.OneToOneField(related_name='extra', primary_key=True, serialize=False, to='problems.Problem', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
