# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0004_auto_20160911_2125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='contestant_own_solutions_access',
            field=models.IntegerField(default=7, verbose_name='contestant\u2019s access to his own solutions', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (7, 'view testing details on sample tests'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')]),
        ),
    ]
