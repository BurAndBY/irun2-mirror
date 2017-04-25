# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0010_auto_20160911_2125'),
        ('quizzes', '0002_auto_20170408_0015'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_available', models.BooleanField(default=False)),
                ('time_limit', models.DurationField()),
                ('tag', models.CharField(max_length=100)),
                ('attempts', models.IntegerField(default=None, null=True, blank=True)),
                ('course', models.ForeignKey(to='courses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='QuizSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField()),
                ('result', models.FloatField(default=0)),
                ('is_finished', models.BooleanField(default=False)),
                ('finish_time', models.DateTimeField(null=True)),
                ('quiz_instance', models.ForeignKey(to='quizzes.QuizInstance')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SessionQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('points', models.FloatField()),
                ('result_points', models.FloatField(default=0)),
                ('question', models.ForeignKey(to='quizzes.Question', on_delete=django.db.models.deletion.PROTECT)),
                ('quiz_session', models.ForeignKey(to='quizzes.QuizSession')),
            ],
        ),
        migrations.CreateModel(
            name='SessionQuestionAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_answer', models.CharField(default=None, max_length=100, null=True)),
                ('is_chosen', models.BooleanField(default=False)),
                ('choice', models.ForeignKey(to='quizzes.Choice', on_delete=django.db.models.deletion.PROTECT)),
                ('session_question', models.ForeignKey(to='quizzes.SessionQuestion')),
            ],
        ),
        migrations.AddField(
            model_name='quiztemplate',
            name='attempts',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='quiztemplate',
            name='time_limit',
            field=models.DurationField(default=datetime.timedelta(0, 1800)),
        ),
        migrations.AddField(
            model_name='quizinstance',
            name='quiz_template',
            field=models.ForeignKey(to='quizzes.QuizTemplate'),
        ),
    ]
