# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solutions', '0006_solution_ip_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='rejudge',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rejudge',
            name='creation_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 1, 20, 17, 38, 21, 591000, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
