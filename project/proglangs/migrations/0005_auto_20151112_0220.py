# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0004_auto_20151112_0210'),
    ]

    operations = [
        migrations.RenameField(
            model_name='compiler',
            old_name='family',
            new_name='language',
        ),
    ]
