# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0006_auto_20161031_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printout',
            name='status',
            field=models.IntegerField(default=1, verbose_name='status', choices=[(0, 'Done'), (1, 'Waiting'), (2, 'Printing'), (3, 'Cancelled')]),
        ),
    ]
