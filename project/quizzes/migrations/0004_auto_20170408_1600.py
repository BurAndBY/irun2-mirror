# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_auto_20170408_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizinstance',
            name='show_answers',
            field=models.BooleanField(default=True, verbose_name='show answers'),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='attempts',
            field=models.IntegerField(default=None, null=True, verbose_name='attempts', blank=True),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='course',
            field=models.ForeignKey(verbose_name='course', to='courses.Course'),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='is_available',
            field=models.BooleanField(default=False, verbose_name='is available'),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='quiz_template',
            field=models.ForeignKey(verbose_name='quiz template', to='quizzes.QuizTemplate'),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='tag',
            field=models.CharField(max_length=100, verbose_name='tag', blank=True),
        ),
        migrations.AlterField(
            model_name='quizinstance',
            name='time_limit',
            field=models.DurationField(verbose_name='time limit'),
        ),
        migrations.AlterField(
            model_name='quiztemplate',
            name='attempts',
            field=models.IntegerField(default=None, null=True, verbose_name='attempts', blank=True),
        ),
        migrations.AlterField(
            model_name='quiztemplate',
            name='name',
            field=models.CharField(unique=True, max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='quiztemplate',
            name='shuffle_questions',
            field=models.BooleanField(default=True, verbose_name='shuffle questions'),
        ),
        migrations.AlterField(
            model_name='quiztemplate',
            name='time_limit',
            field=models.DurationField(default=datetime.timedelta(0, 1800), verbose_name='time limit'),
        ),
    ]
