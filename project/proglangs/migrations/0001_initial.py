# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Compiler',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('handle', models.CharField(unique=True, max_length=30, verbose_name='string identifier')),
                ('language', models.CharField(default=b'', max_length=8, verbose_name='language', blank=True, choices=[(b'', 'Unknown'), (b'c', b'C'), (b'cpp', b'C++'), (b'java', b'Java'), (b'pas', b'Pascal'), (b'dpr', b'Delphi'), (b'py', b'Python'), (b'cs', b'C#')])),
                ('description', models.CharField(max_length=255, verbose_name='description', blank=True)),
                ('legacy', models.BooleanField(default=False, verbose_name='compiler is considered legacy')),
            ],
            options={
                'ordering': ['description'],
            },
        ),
    ]
