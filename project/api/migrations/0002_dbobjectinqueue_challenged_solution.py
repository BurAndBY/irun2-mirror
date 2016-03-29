# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0005_challenge_challengedsolution'),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbobjectinqueue',
            name='challenged_solution',
            field=models.ForeignKey(to='solutions.ChallengedSolution', null=True),
        ),
    ]
