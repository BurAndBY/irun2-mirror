# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0013_auto_20151112_0210'),
    ]

    operations = [
        migrations.RenameField(
            model_name='solution',
            old_name='programming_language',
            new_name='compiler',
        ),
    ]
