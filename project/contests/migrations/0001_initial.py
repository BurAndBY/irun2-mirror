# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import contests.models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0009_auto_20160407_0148'),
        ('storage', '0002_auto_20160306_1931'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proglangs', '0001_initial'),
        ('solutions', '0005_challenge_challengedsolution'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('unauthorized_access', models.IntegerField(default=0, verbose_name='access for unauthorized users', choices=[(0, 'No access'), (1, 'View standings'), (2, 'View standings and problem statements')])),
                ('contestant_own_solutions_access', models.IntegerField(default=3, verbose_name='contestant\u2019s access to his own solutions', choices=[(0, 'no access'), (1, 'view current solution state'), (2, 'view compilation log'), (3, 'view source code'), (4, 'view testing details'), (5, 'view testing details with checker messages'), (6, 'view testing details and test data')])),
                ('attempt_limit', models.PositiveIntegerField(default=100, verbose_name='maximum number of attempts per problem')),
                ('file_size_limit', models.PositiveIntegerField(default=65536, verbose_name='maximum solution file size (bytes)')),
                ('start_time', models.DateTimeField(default=contests.models._default_contest_start_time, verbose_name='start time')),
                ('duration', models.DurationField(default=datetime.timedelta(0, 18000), verbose_name='duration')),
                ('freeze_time', models.DurationField(default=datetime.timedelta(0, 14400), help_text='If not set, there will be no freezing.', null=True, verbose_name='standings freeze time', blank=True)),
                ('show_pending_runs', models.BooleanField(default=True, verbose_name='show pending runs during the freeze time')),
                ('unfreeze_standings', models.BooleanField(default=False, verbose_name='unfreeze standings after the end of the contest')),
                ('enable_upsolving', models.BooleanField(default=False, verbose_name='enable upsolving after the end of the contest')),
                ('compilers', models.ManyToManyField(to='proglangs.Compiler', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContestProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinal_number', models.PositiveIntegerField()),
                ('contest', models.ForeignKey(to='contests.Contest')),
                ('problem', models.ForeignKey(related_name='link_to_contest', to='problems.Problem')),
            ],
            options={
                'ordering': ['ordinal_number'],
            },
        ),
        migrations.CreateModel(
            name='ContestSolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contest', models.ForeignKey(to='contests.Contest')),
                ('fixed_judgement', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='solutions.Judgement', null=True)),
                ('solution', models.OneToOneField(to='solutions.Solution')),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.IntegerField(verbose_name='role', choices=[(0, 'contestant'), (1, 'juror')])),
                ('contest', models.ForeignKey(to='contests.Contest')),
                ('user', models.ForeignKey(related_name='contestmembership', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='contest',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='contests.Membership'),
        ),
        migrations.AddField(
            model_name='contest',
            name='problems',
            field=models.ManyToManyField(to='problems.Problem', through='contests.ContestProblem', blank=True),
        ),
        migrations.AddField(
            model_name='contest',
            name='statements',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='storage.FileMetadata', null=True),
        ),
    ]
