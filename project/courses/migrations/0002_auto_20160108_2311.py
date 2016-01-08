# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='criterion',
            name='label',
            field=models.CharField(unique=True, max_length=8, verbose_name='criterion label'),
        ),
        migrations.AlterField(
            model_name='criterion',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
    ]
