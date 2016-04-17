# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0005_challenge_challengedsolution'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='stop_on_fail',
            field=models.BooleanField(default=False),
        ),
    ]
