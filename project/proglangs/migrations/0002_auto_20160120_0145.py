# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compiler',
            name='description',
            field=models.CharField(max_length=255, verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='compiler',
            name='handle',
            field=models.CharField(unique=True, max_length=30, verbose_name='string identifier'),
        ),
        migrations.AlterField(
            model_name='compiler',
            name='language',
            field=models.CharField(default=b'', max_length=8, verbose_name='language', blank=True, choices=[(b'', 'Unknown'), (b'c', b'C'), (b'cpp', b'C++'), (b'java', b'Java'), (b'pas', b'Pascal'), (b'dpr', b'Delphi'), (b'py', b'Python'), (b'cs', b'C#')]),
        ),
        migrations.AlterField(
            model_name='compiler',
            name='legacy',
            field=models.BooleanField(default=False, verbose_name='compiler is considered legacy'),
        ),
    ]
