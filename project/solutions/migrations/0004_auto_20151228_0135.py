# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0003_auto_20151227_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgementlog',
            name='kind',
            field=models.IntegerField(default=0, choices=[(0, 'Solution compilation log')]),
        ),
    ]
