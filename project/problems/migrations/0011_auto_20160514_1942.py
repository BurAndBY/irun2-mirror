# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('problems', '0010_auto_20160428_0256'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcase',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='testcase',
            name='creation_time',
            field=models.DateTimeField(null=True),
        ),
    ]
