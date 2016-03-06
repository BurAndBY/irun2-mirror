# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.validators


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0005_auto_20160225_0215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='filename',
            field=models.CharField(max_length=255, verbose_name='Filename', validators=[storage.validators.validate_filename]),
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='filename',
            field=models.CharField(max_length=255, verbose_name='Filename', validators=[storage.validators.validate_filename]),
        ),
    ]
