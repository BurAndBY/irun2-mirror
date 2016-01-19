# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_course_enable_sheet'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentCriteriaIntermediate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'courses_assignment_criteria',
                'managed': False,
            },
        ),
        migrations.AlterField(
            model_name='membership',
            name='subgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='subgroup', blank=True, to='courses.Subgroup', null=True),
        ),
    ]
