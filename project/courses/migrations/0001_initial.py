# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
        ('problems', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('kind', models.IntegerField(verbose_name='kind', choices=[(0, 'solving problems within the course'), (1, 'mark'), (2, 'passed or not passed')])),
                ('weight', models.FloatField(default=0.0, verbose_name='weight')),
            ],
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_requirements', models.TextField(max_length=1024, blank=True)),
                ('extra_requirements_ok', models.BooleanField(default=False)),
                ('bonus_attempts', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('compilers', models.ManyToManyField(to='proglangs.Compiler', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Criterion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=8)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.IntegerField(verbose_name='role', choices=[(0, 'student'), (1, 'teacher')])),
                ('course', models.ForeignKey(to='courses.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('course', models.ForeignKey(to='courses.Course')),
                ('criteria', models.ManyToManyField(to='courses.Criterion', verbose_name='criteria', blank=True)),
                ('problem_folder', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='problem folder', to='problems.ProblemFolder', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='slot',
            name='topic',
            field=models.ForeignKey(to='courses.Topic'),
        ),
        migrations.AddField(
            model_name='course',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='courses.Membership'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='criteria',
            field=models.ManyToManyField(to='courses.Criterion', verbose_name='criteria', blank=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='membership',
            field=models.ForeignKey(to='courses.Membership'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='problem',
            field=models.ForeignKey(verbose_name='problem', blank=True, to='problems.Problem', null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='slot',
            field=models.ForeignKey(to='courses.Slot', null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='topic',
            field=models.ForeignKey(to='courses.Topic', null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='course',
            field=models.ForeignKey(to='courses.Course'),
        ),
    ]
