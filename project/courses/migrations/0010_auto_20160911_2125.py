# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_auto_20160812_2252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='student_all_solutions_access',
            field=models.IntegerField(default=1, verbose_name='student\u2019s access to all solutions of the course', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (7, 'view testing details on sample tests'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')]),
        ),
        migrations.AlterField(
            model_name='course',
            name='student_own_solutions_access',
            field=models.IntegerField(default=4, verbose_name='student\u2019s access to his own solutions', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (7, 'view testing details on sample tests'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')]),
        ),
    ]
