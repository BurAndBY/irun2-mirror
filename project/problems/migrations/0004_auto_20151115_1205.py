# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20151023_1959'),
    ]

    operations = [
        migrations.RenameField(
            model_name='testcase',
            old_name='answer_file',
            new_name='answer_resource_id',
        ),
        migrations.RenameField(
            model_name='testcase',
            old_name='input_file',
            new_name='input_resource_id',
        ),
    ]
