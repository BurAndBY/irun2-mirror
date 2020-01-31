# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
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
                ('input_filename', models.CharField(max_length=32, verbose_name='input file name', blank=True)),
                ('output_filename', models.CharField(max_length=32, verbose_name='output file name', blank=True)),
            ],
            options={
                'ordering': ['number', 'subnumber', 'full_name'],
            },
        ),
        migrations.CreateModel(
            name='ProblemFolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='problems.ProblemFolder', null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProblemRelatedFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('size', models.IntegerField()),
                ('resource_id', storage.storage.ResourceIdField()),
                ('file_type', models.IntegerField(verbose_name='file type', choices=[(211, 'TeX statement'), (212, 'HTML statement'), (213, 'Additional statement file'), (214, 'Solution description'), (220, 'Sample input file'), (221, 'Sample output file'), (222, 'User file')])),
                ('description', models.TextField(verbose_name='description')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProblemRelatedSourceFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('size', models.IntegerField()),
                ('resource_id', storage.storage.ResourceIdField()),
                ('file_type', models.IntegerField(verbose_name='file type', choices=[(215, "Author's solution"), (216, 'Checker'), (217, 'Contestant solution'), (218, 'Generator'), (219, 'Library')])),
                ('description', models.TextField(verbose_name='description')),
                ('compiler', models.ForeignKey(verbose_name='compiler', to='proglangs.Compiler', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinal_number', models.PositiveIntegerField(default=0)),
                ('description', models.TextField(blank=True)),
                ('input_resource_id', storage.storage.ResourceIdField()),
                ('input_size', models.IntegerField(default=0)),
                ('answer_resource_id', storage.storage.ResourceIdField()),
                ('answer_size', models.IntegerField(default=0)),
                ('time_limit', models.IntegerField()),
                ('memory_limit', models.IntegerField(default=0)),
                ('points', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='ProblemExtraInfo',
            fields=[
                ('problem', models.OneToOneField(primary_key=True, serialize=False, to='problems.Problem', on_delete=django.db.models.deletion.CASCADE)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('hint', models.TextField(verbose_name='hint', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='testcase',
            name='problem',
            field=models.ForeignKey(to='problems.Problem', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='problemrelatedsourcefile',
            name='problem',
            field=models.ForeignKey(to='problems.Problem', null=True, on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='problemrelatedfile',
            name='problem',
            field=models.ForeignKey(to='problems.Problem', on_delete=django.db.models.deletion.CASCADE),
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
