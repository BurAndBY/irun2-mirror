# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20160106_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfolder',
            name='description',
            field=models.CharField(max_length=255, verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='folder', blank=True, to='users.UserFolder', null=True),
        ),
    ]
