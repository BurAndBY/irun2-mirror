# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JudgementLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_id', storage.storage.ResourceIdField()),
                ('kind', models.IntegerField(default=0, choices=[(0, 'Compilation log')])),
            ],
        ),
        migrations.RemoveField(
            model_name='judgement',
            name='compilation_log',
        ),
        migrations.AddField(
            model_name='judgementlog',
            name='judgement',
            field=models.ForeignKey(to='solutions.Judgement'),
        ),
    ]
