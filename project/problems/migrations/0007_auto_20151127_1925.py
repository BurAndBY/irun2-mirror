# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0006_auto_20151127_1913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='complexity',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='hint',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='offered',
            field=models.TextField(blank=True),
        ),
    ]
