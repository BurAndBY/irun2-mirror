# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0005_solution_author'),
        ('courses', '0002_auto_20160108_2311'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseSolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course', models.ForeignKey(to='courses.Course')),
                ('solution', models.OneToOneField(to='solutions.Solution')),
            ],
        ),
    ]
