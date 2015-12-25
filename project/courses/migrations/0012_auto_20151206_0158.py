# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_auto_20151206_0155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='problem',
            field=models.ForeignKey(verbose_name='problem', blank=True, to='problems.Problem', null=True),
        ),
    ]
