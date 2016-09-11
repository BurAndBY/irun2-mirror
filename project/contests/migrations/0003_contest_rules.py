# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0002_auto_20160415_0138'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='rules',
            field=models.IntegerField(default=1, verbose_name='rules', choices=[(1, b'ACM'), (2, b'IOI')]),
        ),
    ]
