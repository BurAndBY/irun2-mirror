# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0009_auto_20160407_0148'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message_type', models.IntegerField(choices=[(3, 'Question'), (4, 'Answer'), (5, 'Message')])),
                ('timestamp', models.DateTimeField()),
                ('subject', models.CharField(max_length=255, null=True, verbose_name='subject')),
                ('text', models.TextField(max_length=65535, verbose_name='message')),
                ('is_answered', models.BooleanField(default=False)),
                ('contest', models.ForeignKey(to='contests.Contest')),
                ('parent', models.ForeignKey(related_name='+', to='contests.Message', null=True)),
                ('problem', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to='problems.Problem', null=True)),
                ('recipient', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('sender', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MessageUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.ForeignKey(to='contests.Message')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='messageuser',
            unique_together=set([('message', 'user')]),
        ),
    ]
