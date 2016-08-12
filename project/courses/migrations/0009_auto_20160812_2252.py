# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_auto_20160709_1611'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ['academic_year', 'year_of_study', 'group', 'name']},
        ),
    ]
