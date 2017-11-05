# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0004_auto_20170408_1600'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='questiongroup',
            options={'verbose_name': 'Question group'},
        ),
        migrations.AlterModelOptions(
            name='quiztemplate',
            options={'verbose_name': 'Quiz template'},
        ),
        migrations.AlterField(
            model_name='groupquizrelation',
            name='group',
            field=models.ForeignKey(verbose_name='group', to='quizzes.QuestionGroup'),
        ),
        migrations.AlterField(
            model_name='groupquizrelation',
            name='points',
            field=models.FloatField(default=1.0, verbose_name='points'),
        ),
        migrations.AlterField(
            model_name='questiongroup',
            name='name',
            field=models.CharField(unique=True, max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='sessionquestionanswer',
            name='user_answer',
            field=models.CharField(default=None, max_length=200, null=True),
        ),
    ]
