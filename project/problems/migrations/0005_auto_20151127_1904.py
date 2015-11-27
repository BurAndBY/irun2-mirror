# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0004_problem_subnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='subnumber',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
