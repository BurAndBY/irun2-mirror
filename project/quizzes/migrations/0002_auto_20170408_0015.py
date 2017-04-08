# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupQuizRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('points', models.FloatField(default=1.0)),
                ('group', models.ForeignKey(to='quizzes.QuestionGroup')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='QuizTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('shuffle_questions', models.BooleanField(default=True)),
                ('question_groups', models.ManyToManyField(to='quizzes.QuestionGroup', through='quizzes.GroupQuizRelation')),
            ],
        ),
        migrations.AddField(
            model_name='groupquizrelation',
            name='template',
            field=models.ForeignKey(to='quizzes.QuizTemplate'),
        ),
    ]
