# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0003_judgementextrainfo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='judgement',
            name='general_failure_message',
        ),
        migrations.RemoveField(
            model_name='judgement',
            name='general_failure_reason',
        ),
        migrations.AddField(
            model_name='judgementextrainfo',
            name='general_failure_message',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='judgementextrainfo',
            name='general_failure_reason',
            field=models.CharField(default=b'', max_length=64),
        ),
    ]
