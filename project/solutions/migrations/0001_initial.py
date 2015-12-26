# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storage.storage
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
        ('problems', '0001_initial'),
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdHocRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_id', storage.storage.ResourceIdField()),
                ('input_file_name', models.CharField(max_length=80, blank=True)),
                ('output_file_name', models.CharField(max_length=80, blank=True)),
                ('time_limit', models.IntegerField(default=10000)),
                ('memory_limit', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Judgement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=1, choices=[(0, 'Done'), (1, 'Waiting'), (2, 'Preparing'), (3, 'Compiling'), (4, 'Testing'), (5, 'Finishing')])),
                ('outcome', models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Runtime Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')])),
                ('test_number', models.IntegerField(default=0)),
                ('score', models.IntegerField(default=0)),
                ('max_score', models.IntegerField(default=0)),
                ('general_failure_reason', models.IntegerField(default=0)),
                ('general_failure_message', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='JudgementLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_id', storage.storage.ResourceIdField()),
                ('kind', models.IntegerField(default=0, choices=[(0, 'Compilation log')])),
                ('judgement', models.ForeignKey(to='solutions.Judgement')),
            ],
        ),
        migrations.CreateModel(
            name='Rejudge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('committed', models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ad_hoc_run', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='solutions.AdHocRun', null=True)),
                ('best_judgement', models.ForeignKey(related_name='+', to='solutions.Judgement', null=True)),
                ('compiler', models.ForeignKey(to='proglangs.Compiler')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='problems.Problem', null=True)),
                ('source_code', models.ForeignKey(to='storage.FileMetadata')),
            ],
        ),
        migrations.CreateModel(
            name='TestCaseResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('input_resource_id', storage.storage.ResourceIdField(null=True)),
                ('output_resource_id', storage.storage.ResourceIdField(null=True)),
                ('answer_resource_id', storage.storage.ResourceIdField(null=True)),
                ('stdout_resource_id', storage.storage.ResourceIdField(null=True)),
                ('stderr_resource_id', storage.storage.ResourceIdField(null=True)),
                ('exit_code', models.IntegerField()),
                ('time_limit', models.IntegerField(default=0)),
                ('time_used', models.IntegerField()),
                ('memory_limit', models.IntegerField(default=0)),
                ('memory_used', models.IntegerField()),
                ('score', models.IntegerField()),
                ('max_score', models.IntegerField()),
                ('checker_message', models.CharField(max_length=255, blank=True)),
                ('outcome', models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Runtime Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')])),
                ('judgement', models.ForeignKey(to='solutions.Judgement')),
                ('test_case', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='problems.TestCase', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='judgement',
            name='rejudge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, to='solutions.Rejudge', null=True),
        ),
        migrations.AddField(
            model_name='judgement',
            name='solution',
            field=models.ForeignKey(to='solutions.Solution'),
        ),
    ]
