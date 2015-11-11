# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0004_auto_20151107_1620'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AdHocTest',
            new_name='AdHocRun',
        ),
    ]
