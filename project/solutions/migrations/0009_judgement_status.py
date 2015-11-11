# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0008_auto_20151107_1727'),
    ]

    operations = [
        migrations.AddField(
            model_name='judgement',
            name='status',
            field=models.IntegerField(default=1),
        ),
    ]
