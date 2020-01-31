# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0008_auto_20160325_1714'),
        ('solutions', '0003_judgementextrainfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='DbObjectInQueue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('worker', models.CharField(max_length=64, blank=True)),
                ('state', models.IntegerField(default=0, choices=[(0, 'Waiting'), (1, 'Executing'), (2, 'Done')])),
                ('creation_time', models.DateTimeField()),
                ('last_update_time', models.DateTimeField()),
                ('priority', models.IntegerField()),
                ('judgement', models.ForeignKey(to='solutions.Judgement', on_delete=django.db.models.deletion.CASCADE, null=True)),
                ('validation', models.ForeignKey(to='problems.Validation', on_delete=django.db.models.deletion.CASCADE, null=True)),
            ],
        ),
    ]
