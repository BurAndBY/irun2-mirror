# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgement',
            name='outcome',
            field=models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')]),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='outcome',
            field=models.IntegerField(default=0, choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed')]),
        ),
    ]
