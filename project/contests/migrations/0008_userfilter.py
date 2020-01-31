# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0007_auto_20161102_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('regex', models.CharField(max_length=255, verbose_name='regular expression')),
                ('contest', models.ForeignKey(to='contests.Contest', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
    ]
