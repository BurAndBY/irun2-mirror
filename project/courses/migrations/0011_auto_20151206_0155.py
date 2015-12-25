# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_auto_20151206_0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='problem',
            field=models.ForeignKey(verbose_name='problem', to='problems.Problem', null=True),
        ),
    ]
