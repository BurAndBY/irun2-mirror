# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0004_auto_20170408_1600'),
        ('courses', '0010_auto_20160911_2125'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='quiz_instance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='quiz', blank=True, to='quizzes.QuizInstance', null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='kind',
            field=models.IntegerField(verbose_name='kind', choices=[(0, 'solving problems within the course'), (1, 'mark'), (2, 'passed or not passed'), (3, 'quiz result')]),
        ),
    ]
