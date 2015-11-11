# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0012_auto_20151111_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solution',
            name='programming_language',
            field=models.ForeignKey(to='proglangs.Compiler'),
        ),
    ]
