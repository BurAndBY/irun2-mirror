# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0007_auto_20151127_1925'),
        ('courses', '0007_auto_20151203_2206'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('membership', models.ForeignKey(to='courses.Membership')),
                ('problem', models.ForeignKey(to='problems.Problem')),
                ('slot', models.ForeignKey(to='courses.Slot', null=True)),
                ('topic', models.ForeignKey(to='courses.Topic', null=True)),
            ],
        ),
    ]
