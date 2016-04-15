# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plagiarism', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='judgementresult',
            old_name='algo_id',
            new_name='algorithm',
        ),
        migrations.AlterField(
            model_name='aggregatedresult',
            name='id',
            field=models.OneToOneField(primary_key=True, serialize=False, to='solutions.Solution'),
        ),
        migrations.AlterField(
            model_name='algorithm',
            name='id',
            field=models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='judgementresult',
            name='solution_to_compare',
            field=models.ForeignKey(related_name='solution_to_compare', to='solutions.Solution'),
        ),
        migrations.AlterField(
            model_name='judgementresult',
            name='solution_to_judge',
            field=models.ForeignKey(related_name='solution_to_judge', to='solutions.Solution'),
        ),
    ]
