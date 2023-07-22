# Generated by Django 2.2.9 on 2020-02-21 00:02

from django.db import migrations

from storage.resource_id import ResourceIdField


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0012_auto_20200201_0255'),
    ]

    operations = [
        migrations.AlterField('AdHocRun', 'resource_id', ResourceIdField()),
        migrations.AlterField('JudgementLog', 'resource_id', ResourceIdField()),
        migrations.AlterField('TestCaseResult', 'input_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('TestCaseResult', 'output_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('TestCaseResult', 'answer_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('TestCaseResult', 'stdout_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('TestCaseResult', 'stderr_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('Challenge', 'input_resource_id', ResourceIdField()),
        migrations.AlterField('ChallengedSolution', 'output_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('ChallengedSolution', 'stdout_resource_id', ResourceIdField(null=True)),
        migrations.AlterField('ChallengedSolution', 'stderr_resource_id', ResourceIdField(null=True)),
    ]
