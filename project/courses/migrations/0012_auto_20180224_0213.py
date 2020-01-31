# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0011_auto_20170518_1653'),
    ]

    operations = [
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='queue is active')),
                ('name', models.CharField(max_length=255, verbose_name='name', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='QueueEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=0, verbose_name='status', choices=[(0, 'Waiting'), (1, 'In progress'), (2, 'Done')])),
                ('enqueue_time', models.DateTimeField()),
                ('start_time', models.DateTimeField(null=True)),
                ('finish_time', models.DateTimeField(null=True)),
                ('queue', models.ForeignKey(to='courses.Queue', on_delete=django.db.models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='enable_queues',
            field=models.BooleanField(default=False, verbose_name='enable electronic queues'),
        ),
        migrations.AddField(
            model_name='queue',
            name='course',
            field=models.ForeignKey(to='courses.Course', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='queue',
            name='subgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='subgroup', blank=True, to='courses.Subgroup', null=True),
        ),
    ]
