# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0002_solution_receive_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='solution',
            old_name='receive_time',
            new_name='reception_time',
        ),
    ]
