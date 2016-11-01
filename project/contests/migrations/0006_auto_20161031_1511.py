# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contests', '0005_auto_20160911_2154'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContestUserRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('room', models.CharField(max_length=64, verbose_name='room', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Printout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('room', models.CharField(max_length=64, verbose_name='room')),
                ('timestamp', models.DateTimeField()),
                ('text', models.TextField(max_length=65535, verbose_name='text')),
                ('status', models.IntegerField(default=1, choices=[(0, 'Done'), (1, 'Waiting'), (2, 'Printing'), (3, 'Cancelled')])),
            ],
        ),
        migrations.AddField(
            model_name='contest',
            name='enable_printing',
            field=models.BooleanField(default=False, verbose_name='enable printing'),
        ),
        migrations.AddField(
            model_name='contest',
            name='rooms',
            field=models.CharField(max_length=255, verbose_name='rooms (comma-separated)', blank=True),
        ),
        migrations.AddField(
            model_name='printout',
            name='contest',
            field=models.ForeignKey(to='contests.Contest'),
        ),
        migrations.AddField(
            model_name='printout',
            name='user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contestuserroom',
            name='contest',
            field=models.ForeignKey(to='contests.Contest'),
        ),
        migrations.AddField(
            model_name='contestuserroom',
            name='user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='contestuserroom',
            unique_together=set([('contest', 'user')]),
        ),
    ]
