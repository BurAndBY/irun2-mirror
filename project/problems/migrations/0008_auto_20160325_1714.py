# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0007_auto_20160321_1355'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCaseValidation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('input_resource_id', storage.storage.ResourceIdField()),
                ('is_valid', models.BooleanField()),
                ('validator_message', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Validation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_pending', models.BooleanField(default=False)),
                ('general_failure_reason', models.CharField(max_length=64, blank=True)),
                ('problem', models.OneToOneField(to='problems.Problem', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='file_type',
            field=models.IntegerField(verbose_name='file type', choices=[(215, "Author's solution"), (216, 'Checker'), (217, 'Contestant solution'), (218, 'Generator'), (219, 'Library'), (223, 'Validator')]),
        ),
        migrations.AddField(
            model_name='validation',
            name='validator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='problems.ProblemRelatedSourceFile', null=True),
        ),
        migrations.AddField(
            model_name='testcasevalidation',
            name='validation',
            field=models.ForeignKey(to='problems.Validation', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
