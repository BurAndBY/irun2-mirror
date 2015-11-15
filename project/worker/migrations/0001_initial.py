# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=0, choices=[(0, b'Enqueued'), (1, b'Processing'), (2, b'Done')])),
                ('stage', models.IntegerField(default=0)),
                ('on_stage_progress', models.IntegerField(default=0)),
                ('on_stage_max', models.IntegerField(default=0)),
                ('x', models.IntegerField()),
            ],
        ),
    ]
