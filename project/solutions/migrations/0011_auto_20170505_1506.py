# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0010_auto_20161102_0202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='memory_limit',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='challengedsolution',
            name='memory_used',
            field=models.BigIntegerField(null=True),
        ),
    ]
