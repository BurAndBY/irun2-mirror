# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import storage.resource_id


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('size', models.IntegerField()),
                ('resource_id', storage.resource_id.ResourceIdFieldDeprecated()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
