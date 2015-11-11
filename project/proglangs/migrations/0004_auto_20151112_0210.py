# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0013_auto_20151112_0210'),
        ('proglangs', '0003_auto_20151023_2051'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compiler',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('handle', models.CharField(unique=True, max_length=30)),
                ('family', models.CharField(default=b'', max_length=8, blank=True, choices=[(b'', b'Unknown'), (b'c', b'C'), (b'cpp', b'C++'), (b'java', b'Java'), (b'pas', b'Pascal'), (b'dpr', b'Delphi'), (b'py', b'Python'), (b'cs', b'C#')])),
                ('description', models.CharField(max_length=255, blank=True)),
                ('legacy', models.BooleanField(default=False)),
            ],
        ),
        migrations.DeleteModel(
            name='ProgrammingLanguage',
        ),
    ]
