# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='programminglanguage',
            old_name='obsolete',
            new_name='legacy',
        ),
    ]
