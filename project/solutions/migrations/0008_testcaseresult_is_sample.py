# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0007_judgement_judgement_before'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcaseresult',
            name='is_sample',
            field=models.BooleanField(default=False),
        ),
    ]
