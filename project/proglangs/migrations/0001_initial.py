# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProgrammingLanguage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('handle', models.CharField(max_length=30)),
                ('family', models.CharField(default=b'', max_length=8, blank=True, choices=[(b'', b'Unknown'), (b'cpp', b'C/C++'), (b'java', b'Java'), (b'pascal', b'Pascal'), (b'delphi', b'Delphi'), (b'py', b'Python'), (b'cs', b'C#')])),
                ('description', models.CharField(max_length=255, blank=True)),
                ('obsolete', models.BooleanField(default=False)),
            ],
        ),
    ]
