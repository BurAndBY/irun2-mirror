# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_compilers'),
    ]

    operations = [
        migrations.CreateModel(
            name='Criterion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=8)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('topic', models.ForeignKey(to='courses.Topic')),
            ],
        ),
        migrations.AlterField(
            model_name='course',
            name='compilers',
            field=models.ManyToManyField(to='proglangs.Compiler', blank=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='criteria',
            field=models.ManyToManyField(to='courses.Criterion', blank=True),
        ),
    ]
