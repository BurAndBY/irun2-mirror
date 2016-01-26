# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_auto_20160126_1726'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemExtraInfo',
            fields=[
                ('problem', models.OneToOneField(primary_key=True, serialize=False, to='problems.Problem')),
                ('offered', models.CharField(max_length=255, verbose_name='where the problem was offered', blank=True)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('hint', models.TextField(verbose_name='hint', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='problem',
            name='description',
        ),
        migrations.RemoveField(
            model_name='problem',
            name='hint',
        ),
        migrations.RemoveField(
            model_name='problem',
            name='offered',
        ),
        migrations.AlterField(
            model_name='problemfolder',
            name='name',
            field=models.CharField(max_length=64),
        ),
    ]
