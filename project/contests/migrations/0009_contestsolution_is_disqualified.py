# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0008_userfilter'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestsolution',
            name='is_disqualified',
            field=models.BooleanField(default=False),
        ),
    ]
