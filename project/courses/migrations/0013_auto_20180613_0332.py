# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0012_auto_20180224_0213'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='status',
            field=models.IntegerField(default=0, verbose_name='status', choices=[(0, 'Running'), (1, 'Archived')]),
        ),
        migrations.AlterField(
            model_name='queueentry',
            name='enqueue_time',
            field=models.DateTimeField(verbose_name='enqueue time'),
        ),
    ]
