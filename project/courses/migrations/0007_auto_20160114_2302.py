# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_auto_20160114_2300'),
    ]

    operations = [
        migrations.AddField(
            model_name='subgroup',
            name='course',
            field=models.ForeignKey(default=None, to='courses.Course'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subgroup',
            name='name',
            field=models.CharField(max_length=16, blank=True),
        ),
    ]
