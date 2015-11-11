# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0002_auto_20151107_1615'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adhoctest',
            old_name='handle',
            new_name='resource_id',
        ),
        migrations.RenameField(
            model_name='solution',
            old_name='handle',
            new_name='resource_id',
        ),
        migrations.RenameField(
            model_name='testcaseresult',
            old_name='answer_handle',
            new_name='answer_resource_id',
        ),
        migrations.RenameField(
            model_name='testcaseresult',
            old_name='input_handle',
            new_name='input_resource_id',
        ),
        migrations.RenameField(
            model_name='testcaseresult',
            old_name='output_handle',
            new_name='output_resource_id',
        ),
        migrations.RenameField(
            model_name='testcaseresult',
            old_name='stderr_handle',
            new_name='stderr_resource_id',
        ),
        migrations.RenameField(
            model_name='testcaseresult',
            old_name='stdout_handle',
            new_name='stdout_resource_id',
        ),
    ]
