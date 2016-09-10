# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0008_testcaseresult_is_sample'),
    ]

    operations = [
        migrations.AddField(
            model_name='judgement',
            name='sample_tests_passed',
            field=models.NullBooleanField(default=None),
        ),
    ]
