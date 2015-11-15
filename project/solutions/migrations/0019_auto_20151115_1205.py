# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0018_auto_20151115_0301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgement',
            name='status',
            field=models.IntegerField(default=1, choices=[(0, 'Done'), (1, 'Waiting'), (2, 'Preparing'), (3, 'Compiling'), (4, 'Testing'), (5, 'Finishing')]),
        ),
    ]
