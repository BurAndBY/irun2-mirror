# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompilerDetails',
            fields=[
                ('compiler', models.OneToOneField(primary_key=True, serialize=False, to='proglangs.Compiler')),
                ('compile_command', models.CharField(max_length=255, verbose_name='compile command', blank=True)),
                ('run_command', models.CharField(max_length=255, verbose_name='run command', blank=True)),
            ],
        ),
    ]
