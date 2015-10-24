# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20151023_1959'),
        ('proglangs', '0003_auto_20151023_2051'),
    ]

    operations = [
        migrations.CreateModel(
            name='Judgement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('compilation_log', storage.storage.ResourceIdField()),
                ('score', models.IntegerField()),
                ('max_score', models.IntegerField()),
                ('outcome', models.IntegerField()),
                ('is_accepted', models.BooleanField()),
                ('general_failure_reason', models.IntegerField()),
                ('general_failure_message', models.CharField(max_length=255)),
                ('problem', models.ForeignKey(to='problems.Problem', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SimpleTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('handle', storage.storage.ResourceIdField()),
                ('input_file_name', models.CharField(max_length=80, blank=True)),
                ('output_file_name', models.CharField(max_length=80, blank=True)),
                ('time_limit', models.IntegerField(default=10000)),
                ('memory_limit', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=256, blank=True)),
                ('handle', storage.storage.ResourceIdField()),
                ('programming_language', models.ForeignKey(to='proglangs.ProgrammingLanguage')),
            ],
        ),
        migrations.CreateModel(
            name='TestCaseResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('input_handle', storage.storage.ResourceIdField()),
                ('output_handle', storage.storage.ResourceIdField()),
                ('answer_handle', storage.storage.ResourceIdField()),
                ('stdout_handle', storage.storage.ResourceIdField()),
                ('stderr_handle', storage.storage.ResourceIdField()),
                ('exit_code', models.IntegerField()),
                ('time_limit', models.IntegerField(null=True)),
                ('time_used', models.IntegerField()),
                ('memory_limit', models.IntegerField(null=True)),
                ('memory_used', models.IntegerField()),
                ('score', models.IntegerField()),
                ('max_score', models.IntegerField()),
                ('checker_message', models.CharField(max_length=255, blank=True)),
                ('outcome', models.IntegerField()),
                ('check_failed_reason', models.IntegerField()),
                ('judgement', models.ForeignKey(to='solutions.Judgement')),
            ],
        ),
        migrations.AddField(
            model_name='judgement',
            name='simple_test',
            field=models.ForeignKey(to='solutions.SimpleTest', null=True),
        ),
        migrations.AddField(
            model_name='judgement',
            name='solution',
            field=models.ForeignKey(to='solutions.Solution'),
        ),
    ]
