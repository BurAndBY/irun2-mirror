# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0017_auto_20151114_1226'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rejudge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('committed', models.NullBooleanField()),
            ],
        ),
        migrations.AddField(
            model_name='judgement',
            name='rejudge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='solutions.Rejudge', null=True),
        ),
    ]
