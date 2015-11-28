# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_auto_20151128_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackmessage',
            name='when',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 28, 15, 48, 50, 236000, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
