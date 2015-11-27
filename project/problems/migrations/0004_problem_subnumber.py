# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_problem_folders'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='subnumber',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
