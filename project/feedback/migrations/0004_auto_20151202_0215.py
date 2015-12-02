# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_feedbackmessage_when'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackmessage',
            name='attachment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='attachment', to='storage.FileMetadata', null=True),
        ),
        migrations.AlterField(
            model_name='feedbackmessage',
            name='body',
            field=models.TextField(max_length=1024, verbose_name='message body'),
        ),
        migrations.AlterField(
            model_name='feedbackmessage',
            name='subject',
            field=models.CharField(max_length=255, verbose_name='subject', blank=True),
        ),
    ]
