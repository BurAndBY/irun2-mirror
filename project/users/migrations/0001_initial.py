# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('description', models.CharField(max_length=255, verbose_name='description', blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='users.UserFolder', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('patronymic', models.CharField(max_length=30, verbose_name='patronymic', blank=True)),
                ('needs_change_password', models.BooleanField(default=False, verbose_name='password needs to be changed by user')),
                ('description', models.CharField(max_length=255, verbose_name='description', blank=True)),
                ('has_api_access', models.BooleanField(default=False, verbose_name='API access')),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='folder', blank=True, to='users.UserFolder', null=True)),
                ('last_used_compiler', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='last used compiler', blank=True, to='proglangs.Compiler', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='userfolder',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
