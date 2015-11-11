# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20151023_1959'),
        ('solutions', '0005_auto_20151107_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='ad_hoc_run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='solutions.AdHocRun', null=True),
        ),
        migrations.AddField(
            model_name='solution',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='problems.Problem', null=True),
        ),
    ]
