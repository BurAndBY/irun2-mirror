# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0002_auto_20151023_2025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programminglanguage',
            name='handle',
            field=models.CharField(unique=True, max_length=30),
        ),
    ]
