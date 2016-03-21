# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0006_auto_20160306_1931'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='problemrelatedfile',
            unique_together=set([('problem', 'filename')]),
        ),
        migrations.AlterUniqueTogether(
            name='problemrelatedsourcefile',
            unique_together=set([('problem', 'filename')]),
        ),
    ]
