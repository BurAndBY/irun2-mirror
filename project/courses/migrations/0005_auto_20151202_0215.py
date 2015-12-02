# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_topic_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.IntegerField(verbose_name='kind', choices=[(0, 'Problem solving'), (1, 'Mark'), (2, 'Passed or not passed')])),
                ('weight', models.FloatField(verbose_name='weight')),
            ],
        ),
        migrations.AlterField(
            model_name='course',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='criteria',
            field=models.ManyToManyField(to='courses.Criterion', verbose_name='criteria', blank=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='problem_folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='problem folder', to='problems.ProblemFolder', null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='course',
            field=models.ForeignKey(to='courses.Course'),
        ),
    ]
