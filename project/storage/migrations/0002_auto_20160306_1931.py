# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.validators


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filemetadata',
            name='filename',
            field=models.CharField(max_length=255, verbose_name='Filename', validators=[storage.validators.validate_filename]),
        ),
    ]
