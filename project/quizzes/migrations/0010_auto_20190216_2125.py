# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-02-16 18:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0009_auto_20190209_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='kind',
            field=models.IntegerField(choices=[(0, 'Single correct answer'), (1, 'Multiple correct answers'), (2, 'Text answer'), (3, 'Open answer')], default=0),
        ),
        migrations.AlterField(
            model_name='sessionquestionanswer',
            name='choice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='quizzes.Choice'),
        ),
    ]
