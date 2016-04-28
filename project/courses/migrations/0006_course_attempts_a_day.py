# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_course_common_problems'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='attempts_a_day',
            field=models.PositiveIntegerField(default=5, null=True, verbose_name='Number of attempts a day per problem', blank=True),
        ),
    ]
