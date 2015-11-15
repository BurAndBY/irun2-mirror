# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=8)),
                ('full_name', models.CharField(max_length=200, blank=True)),
                ('short_name', models.CharField(max_length=32, blank=True)),
                ('complexity', models.IntegerField(null=True)),
                ('offered', models.TextField()),
                ('description', models.TextField()),
                ('hint', models.TextField()),
                ('input_filename', models.CharField(max_length=32, blank=True)),
                ('output_filename', models.CharField(max_length=32, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProblemRelatedFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_type', models.IntegerField(default=222, choices=[(222, b'User File'), (218, b'Generator'), (212, b'HTML Statement'), (211, b'TeX Statement'), (219, b'Library'), (216, b'Checker'), (214, b'Solution Description'), (215, b"Author's Solution")])),
                ('is_public', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=100)),
                ('size', models.IntegerField()),
                ('description', models.TextField()),
                ('resource_id', storage.storage.ResourceIdField()),
                ('problem', models.ForeignKey(to='problems.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinal_number', models.PositiveIntegerField(default=0)),
                ('description', models.TextField()),
                ('input_resource_id', storage.storage.ResourceIdField()),
                ('input_size', models.IntegerField(default=0)),
                ('answer_resource_id', storage.storage.ResourceIdField()),
                ('answer_size', models.IntegerField(default=0)),
                ('time_limit', models.IntegerField()),
                ('memory_limit', models.IntegerField(default=0)),
                ('points', models.IntegerField(default=1)),
                ('problem', models.ForeignKey(to='problems.Problem')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='testcase',
            unique_together=set([('problem', 'ordinal_number')]),
        ),
    ]
