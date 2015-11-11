# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0007_solution_best_judgement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgement',
            name='general_failure_reason',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='judgement',
            name='is_accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='judgement',
            name='max_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='judgement',
            name='outcome',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='judgement',
            name='score',
            field=models.IntegerField(default=0),
        ),
    ]
