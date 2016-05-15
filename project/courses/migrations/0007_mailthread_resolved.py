# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_course_attempts_a_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailthread',
            name='resolved',
            field=models.BooleanField(default=True),
        ),
    ]
