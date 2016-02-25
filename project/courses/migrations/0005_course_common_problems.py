# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0005_auto_20160225_0215'),
        ('courses', '0004_auto_20160224_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='common_problems',
            field=models.ManyToManyField(to='problems.Problem', blank=True),
        ),
    ]
