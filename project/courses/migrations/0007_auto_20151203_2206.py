# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0006_activity_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.IntegerField(verbose_name='role', choices=[(0, 'student'), (1, 'teacher')])),
                ('course', models.ForeignKey(to='courses.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='activity',
            name='kind',
            field=models.IntegerField(verbose_name='kind', choices=[(0, 'solving problems within the course'), (1, 'mark'), (2, 'passed or not passed')]),
        ),
        migrations.AlterField(
            model_name='activity',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='weight',
            field=models.FloatField(default=0.0, verbose_name='weight'),
        ),
        migrations.AddField(
            model_name='course',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='courses.Membership'),
        ),
    ]
