# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('worker', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='state',
        ),
        migrations.AddField(
            model_name='job',
            name='status',
            field=models.IntegerField(default=0, choices=[(0, b'Enqueued'), (1, b'Processing'), (2, b'Done')]),
        ),
        migrations.AlterField(
            model_name='job',
            name='on_stage_max',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='job',
            name='on_stage_progress',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='job',
            name='stage',
            field=models.IntegerField(default=0),
        ),
    ]
