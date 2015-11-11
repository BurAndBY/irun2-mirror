# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0010_auto_20151111_0015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testcaseresult',
            name='check_failed_reason',
        ),
    ]
