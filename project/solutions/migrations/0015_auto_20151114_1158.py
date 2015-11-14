# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0014_auto_20151112_0220'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='judgement',
            name='is_accepted',
        ),
        migrations.AddField(
            model_name='judgement',
            name='test_number',
            field=models.IntegerField(default=0),
        ),
    ]
