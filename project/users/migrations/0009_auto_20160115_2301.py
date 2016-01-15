# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20160112_0104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='last_used_compiler',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='last used compiler', blank=True, to='proglangs.Compiler', null=True),
        ),
    ]
