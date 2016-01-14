# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_activity_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subgroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=16)),
            ],
        ),
        migrations.AddField(
            model_name='membership',
            name='subgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='subgroup', to='courses.Subgroup', null=True),
        ),
    ]
