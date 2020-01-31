# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_auto_20160206_1444'),
        ('storage', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0002_auto_20160129_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('body', models.TextField(max_length=65535, verbose_name='message')),
                ('attachment', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='attachment', to='storage.FileMetadata', null=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='MailThread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=255, verbose_name='subject', blank=True)),
                ('last_message_timestamp', models.DateTimeField()),
                ('course', models.ForeignKey(to='courses.Course', on_delete=django.db.models.deletion.CASCADE)),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.CASCADE)),
                ('problem', models.ForeignKey(to='problems.Problem', null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='MailUserThreadVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('thread', models.ForeignKey(to='courses.MailThread', on_delete=django.db.models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='mailmessage',
            name='thread',
            field=models.ForeignKey(to='courses.MailThread', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='mailuserthreadvisit',
            unique_together=set([('user', 'thread')]),
        ),
    ]
