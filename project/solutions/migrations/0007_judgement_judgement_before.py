# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0006_solution_stop_on_fail'),
    ]

    operations = [
        migrations.AddField(
            model_name='judgement',
            name='judgement_before',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, default=None, to='solutions.Judgement', null=True),
        ),
    ]
