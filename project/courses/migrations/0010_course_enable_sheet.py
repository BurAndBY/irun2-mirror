# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_auto_20160115_2301'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='enable_sheet',
            field=models.BooleanField(default=False, verbose_name='enable mark sheet'),
        ),
    ]
