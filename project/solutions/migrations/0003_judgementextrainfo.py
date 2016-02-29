# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0002_auto_20160225_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='JudgementExtraInfo',
            fields=[
                ('judgement', models.OneToOneField(related_name='extra_info', primary_key=True, serialize=False, to='solutions.Judgement')),
                ('creation_time', models.DateTimeField(null=True)),
                ('start_testing_time', models.DateTimeField(null=True)),
                ('finish_testing_time', models.DateTimeField(null=True)),
            ],
        ),
    ]
