# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0007_auto_20151127_1925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='complexity',
            field=models.IntegerField(default=None, null=True, verbose_name='complexity', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='description',
            field=models.TextField(verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='folders',
            field=models.ManyToManyField(to='problems.ProblemFolder', verbose_name='folders'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='full_name',
            field=models.CharField(max_length=200, verbose_name='full name', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='hint',
            field=models.TextField(verbose_name='hint', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='input_filename',
            field=models.CharField(max_length=32, verbose_name='input file name', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='number',
            field=models.IntegerField(default=None, null=True, verbose_name='number', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='offered',
            field=models.TextField(verbose_name='where the problem was offered', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='output_filename',
            field=models.CharField(max_length=32, verbose_name='output file name', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='short_name',
            field=models.CharField(max_length=32, verbose_name='short name', blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='subnumber',
            field=models.IntegerField(default=None, null=True, verbose_name='subnumber', blank=True),
        ),
        migrations.AlterField(
            model_name='problemrelatedfile',
            name='file_type',
            field=models.IntegerField(default=222, choices=[(222, 'User file'), (218, 'Generator'), (212, 'HTML statement'), (211, 'TeX statement'), (219, 'Library'), (216, 'Checker'), (214, 'Solution description'), (215, "Author's solution")]),
        ),
    ]
