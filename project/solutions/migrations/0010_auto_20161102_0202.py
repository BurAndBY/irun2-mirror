# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0009_judgement_sample_tests_passed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcaseresult',
            name='memory_limit',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='memory_used',
            field=models.BigIntegerField(),
        ),
    ]
