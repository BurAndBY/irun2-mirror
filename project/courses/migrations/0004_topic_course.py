# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_auto_20151127_0215'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='course',
            field=models.ForeignKey(default=1, to='courses.Course'),
            preserve_default=False,
        ),
    ]
