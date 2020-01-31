# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0005_challenge_challengedsolution'),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregatedResult',
            fields=[
                ('id', models.OneToOneField(primary_key=True, serialize=False, to='solutions.Solution', on_delete=django.db.models.deletion.CASCADE)),
                ('relevance', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Algorithm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('enabled', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='JudgementResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('similarity', models.FloatField()),
                ('verdict', models.CharField(max_length=2048)),
                ('algorithm', models.ForeignKey(to='plagiarism.Algorithm', on_delete=django.db.models.deletion.CASCADE)),
                ('solution_to_compare', models.ForeignKey(related_name='solution_to_compare', to='solutions.Solution', on_delete=django.db.models.deletion.CASCADE)),
                ('solution_to_judge', models.ForeignKey(related_name='solution_to_judge', to='solutions.Solution', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
    ]
