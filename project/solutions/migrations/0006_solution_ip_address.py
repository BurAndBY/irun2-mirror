# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0005_solution_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='ip_address',
            field=models.GenericIPAddressField(null=True, blank=True),
        ),
    ]
