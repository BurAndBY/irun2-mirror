# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0009_contestsolution_is_disqualified'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='kind',
            field=models.IntegerField(default=0, verbose_name='kind', choices=[(0, 'Not set'), (1, 'Official contest'), (2, 'Trial tour'), (3, 'Qualifying tour'), (4, 'Training')]),
        ),
    ]
