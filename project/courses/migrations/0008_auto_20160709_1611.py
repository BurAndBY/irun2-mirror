# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_mailthread_resolved'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='academic_year',
            field=models.PositiveIntegerField(null=True, verbose_name='Academic year', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='group',
            field=models.PositiveIntegerField(null=True, verbose_name='Group number', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='year_of_study',
            field=models.PositiveIntegerField(null=True, verbose_name='Year of study', blank=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name', blank=True),
        ),
    ]
