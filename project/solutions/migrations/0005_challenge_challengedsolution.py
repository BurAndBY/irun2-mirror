# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.storage
import django.db.models.deletion
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0008_auto_20160325_1714'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solutions', '0004_auto_20160327_1203'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('time_limit', models.IntegerField()),
                ('memory_limit', models.IntegerField(default=0)),
                ('input_resource_id', storage.storage.ResourceIdField()),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('problem', models.ForeignKey(to='problems.Problem', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ChallengedSolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outcome', models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')])),
                ('output_resource_id', storage.storage.ResourceIdField(null=True)),
                ('stdout_resource_id', storage.storage.ResourceIdField(null=True)),
                ('stderr_resource_id', storage.storage.ResourceIdField(null=True)),
                ('exit_code', models.IntegerField(null=True)),
                ('time_used', models.IntegerField(null=True)),
                ('memory_used', models.IntegerField(null=True)),
                ('challenge', models.ForeignKey(to='solutions.Challenge', on_delete=django.db.models.deletion.CASCADE)),
                ('solution', models.ForeignKey(to='solutions.Solution', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
    ]
