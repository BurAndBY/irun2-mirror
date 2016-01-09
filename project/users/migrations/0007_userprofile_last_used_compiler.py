# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
        ('users', '0006_userprofile_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_used_compiler',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='last used compiler', to='proglangs.Compiler', null=True),
        ),
    ]
