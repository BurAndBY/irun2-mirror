# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_assignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='criteria',
            field=models.ManyToManyField(to='courses.Criterion', verbose_name='criteria', blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='problem',
            field=models.ForeignKey(verbose_name='problem', to='problems.Problem'),
        ),
    ]
