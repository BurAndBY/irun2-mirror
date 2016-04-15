# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.storage
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0001_initial')
    ]

    operations = [
        migrations.CreateModel(
            name='Algorithm',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('enabled', models.BooleanField()),              
            ],
        ),
        migrations.CreateModel(
            name='JudgementResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('solution_to_judge', models.ForeignKey(to='solutions.Solution')),
                ('solution_to_compare', models.ForeignKey(to='solutions.Solution')),
                ('algo_id', models.ForeignKey(to='plagiarism.Algorithm')),
                ('similarity', models.FloatField()),
                ('verdict', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='AggregatedResult',
            fields=[
                ('id', models.ForeignKey(to='solutions.Solution', primary_key=True)),
                ('relevance', models.FloatField()),
            ],
        ),
    ]
