# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField(default=None, null=True, verbose_name='number', blank=True)),
                ('subnumber', models.IntegerField(default=None, null=True, verbose_name='subnumber', blank=True)),
                ('full_name', models.CharField(max_length=200, verbose_name='full name', blank=True)),
                ('short_name', models.CharField(max_length=32, verbose_name='short name', blank=True)),
                ('complexity', models.IntegerField(default=None, null=True, verbose_name='complexity', blank=True)),
                ('offered', models.TextField(verbose_name='where the problem was offered', blank=True)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('hint', models.TextField(verbose_name='hint', blank=True)),
                ('input_filename', models.CharField(max_length=32, verbose_name='input file name', blank=True)),
                ('output_filename', models.CharField(max_length=32, verbose_name='output file name', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProblemFolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='problems.ProblemFolder', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProblemRelatedFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_type', models.IntegerField(default=222, choices=[(222, 'User file'), (218, 'Generator'), (212, 'HTML statement'), (211, 'TeX statement'), (219, 'Library'), (216, 'Checker'), (214, 'Solution description'), (215, "Author's solution")])),
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
        migrations.AddField(
            model_name='problem',
            name='folders',
            field=models.ManyToManyField(to='problems.ProblemFolder', verbose_name='folders'),
        ),
        migrations.AlterUniqueTogether(
            name='testcase',
            unique_together=set([('problem', 'ordinal_number')]),
        ),
    ]
