# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('subject', models.CharField(max_length=255, verbose_name='subject', blank=True)),
                ('body', models.TextField(max_length=1024, verbose_name='message body')),
                ('attachment', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='attachment', to='storage.FileMetadata', null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
