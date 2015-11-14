# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0015_auto_20151114_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcaseresult',
            name='outcome',
            field=models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Runtime Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')]),
        ),
    ]
