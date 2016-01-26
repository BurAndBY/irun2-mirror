# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0002_auto_20160120_0145'),
        ('problems', '0005_auto_20160126_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemrelatedsourcefile',
            name='compiler',
            field=models.ForeignKey(default=20014, verbose_name='compiler', to='proglangs.Compiler'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='description',
            field=models.TextField(verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='file_type',
            field=models.IntegerField(verbose_name='file type', choices=[(211, 'TeX statement'), (212, 'HTML statement'), (213, 'Additional statement file'), (214, 'Solution description'), (220, 'Sample input file'), (221, 'Sample output file'), (222, 'User file')]),
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='description',
            field=models.TextField(verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='problemrelatedsourcefile',
            name='file_type',
            field=models.IntegerField(verbose_name='file type', choices=[(215, "Author's solution"), (216, 'Checker'), (217, 'Contestant solution'), (218, 'Generator'), (219, 'Library')]),
        ),
    ]
