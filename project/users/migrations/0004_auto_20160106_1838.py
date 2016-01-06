# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20160106_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='needs_change_password',
            field=models.BooleanField(default=False, verbose_name='password needs to be changed'),
        ),
    ]
