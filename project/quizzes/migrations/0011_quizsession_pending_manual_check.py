# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-02-16 18:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0010_auto_20190216_2125'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizsession',
            name='pending_manual_check',
            field=models.BooleanField(default=False),
        ),
    ]
