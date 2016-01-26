# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_delete_auditrecord'),
        ('problems', '0004_remove_problemextrainfo_offered'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemRelatedSourceFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_type', models.IntegerField(choices=[(215, "Author's solution"), (216, 'Checker'), (217, 'Contestant solution'), (218, 'Generator'), (219, 'Library')])),
                ('description', models.TextField()),
                ('attachment', models.ForeignKey(to='storage.FileMetadata')),
                ('problem', models.ForeignKey(to='problems.Problem')),
            ],
        ),
        migrations.RemoveField(
            model_name='problemrelatedfile',
            name='is_public',
        ),
        migrations.RemoveField(
            model_name='problemrelatedfile',
            name='name',
        ),
        migrations.RemoveField(
            model_name='problemrelatedfile',
            name='resource_id',
        ),
        migrations.RemoveField(
            model_name='problemrelatedfile',
            name='size',
        ),
        migrations.AddField(
            model_name='problemrelatedfile',
            name='attachment',
            field=models.ForeignKey(default=1, to='storage.FileMetadata'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='file_type',
            field=models.IntegerField(choices=[(211, 'TeX statement'), (212, 'HTML statement'), (213, 'Additional statement file'), (214, 'Solution description'), (220, 'Sample input file'), (221, 'Sample output file'), (222, 'User file')]),
        ),
    ]
