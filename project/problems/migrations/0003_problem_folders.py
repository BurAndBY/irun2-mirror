# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_problemfolder'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='folders',
            field=models.ManyToManyField(to='problems.ProblemFolder'),
        ),
    ]
