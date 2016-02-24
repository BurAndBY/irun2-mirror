# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20160224_2023'),
    ]

    operations = [
        migrations.RenameField(
            model_name='problem',
            old_name='complexity',
            new_name='difficulty',
        ),
    ]
