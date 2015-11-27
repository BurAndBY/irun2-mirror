# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0005_auto_20151127_1904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='number',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
