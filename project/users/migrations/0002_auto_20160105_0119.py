# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='userfolder',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='folder', to='users.UserFolder', null=True),
        ),
    ]
