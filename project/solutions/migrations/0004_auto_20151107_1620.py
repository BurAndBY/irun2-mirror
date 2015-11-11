# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0003_auto_20151107_1619'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='judgement',
            name='problem',
        ),
        migrations.RemoveField(
            model_name='judgement',
            name='simple_test',
        ),
    ]
