# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
        ('problems', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solutions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentCriteriaIntermediate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'courses_assignment_criteria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('description', models.TextField(max_length=255, verbose_name='description', blank=True)),
                ('kind', models.IntegerField(verbose_name='kind', choices=[(0, 'solving problems within the course'), (1, 'mark'), (2, 'passed or not passed')])),
                ('weight', models.FloatField(default=0.0, verbose_name='weight')),
            ],
        ),
        migrations.CreateModel(
            name='ActivityRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mark', models.IntegerField(default=0)),
                ('enum', models.IntegerField(default=0, choices=[(0, b''), (1, 'pass'), (2, 'no pass'), (3, 'absence')])),
                ('activity', models.ForeignKey(to='courses.Activity')),
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
                ('student_own_solutions_access', models.IntegerField(default=4, verbose_name='student\u2019s access to his own solutions', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')])),
                ('student_all_solutions_access', models.IntegerField(default=1, verbose_name='student\u2019s access to all solutions of the course', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')])),
                ('enable_sheet', models.BooleanField(default=False, verbose_name='enable mark sheet')),
                ('compilers', models.ManyToManyField(to='proglangs.Compiler', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseSolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course', models.ForeignKey(to='courses.Course')),
                ('solution', models.OneToOneField(to='solutions.Solution')),
            ],
        ),
        migrations.CreateModel(
            name='Criterion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(unique=True, max_length=8, verbose_name='criterion label')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.IntegerField(verbose_name='role', choices=[(0, 'student'), (1, 'teacher')])),
                ('course', models.ForeignKey(to='courses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subgroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=16)),
                ('course', models.ForeignKey(to='courses.Course')),
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
            model_name='membership',
            name='subgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='subgroup', blank=True, to='courses.Subgroup', null=True),
        ),
        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
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
            model_name='activityrecord',
            name='membership',
            field=models.ForeignKey(to='courses.Membership'),
        ),
        migrations.AddField(
            model_name='activity',
            name='course',
            field=models.ForeignKey(to='courses.Course'),
        ),
    ]
