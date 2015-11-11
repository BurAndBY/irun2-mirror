# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0011_remove_testcaseresult_check_failed_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcaseresult',
            name='answer_resource_id',
            field=storage.storage.ResourceIdField(null=True),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='input_resource_id',
            field=storage.storage.ResourceIdField(null=True),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='output_resource_id',
            field=storage.storage.ResourceIdField(null=True),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='stderr_resource_id',
            field=storage.storage.ResourceIdField(null=True),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='stdout_resource_id',
            field=storage.storage.ResourceIdField(null=True),
        ),
    ]
