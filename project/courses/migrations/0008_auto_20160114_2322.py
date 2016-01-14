# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_auto_20160114_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subgroup',
            name='name',
            field=models.CharField(max_length=16),
        ),
    ]
