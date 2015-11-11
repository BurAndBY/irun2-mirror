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
                ('state', models.IntegerField(choices=[(0, b'Enqueued'), (1, b'Processing'), (2, b'Done')])),
                ('stage', models.IntegerField()),
                ('on_stage_progress', models.IntegerField()),
                ('on_stage_max', models.IntegerField()),
                ('x', models.IntegerField()),
            ],
        ),
    ]
