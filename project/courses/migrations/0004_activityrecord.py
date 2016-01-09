# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_coursesolution'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mark', models.IntegerField(default=0)),
                ('enum', models.IntegerField(default=0, choices=[(0, ''), (1, 'pass'), (2, 'no pass'), (3, 'absence')])),
                ('activity', models.ForeignKey(to='courses.Activity')),
                ('membership', models.ForeignKey(to='courses.Membership')),
            ],
        ),
    ]
