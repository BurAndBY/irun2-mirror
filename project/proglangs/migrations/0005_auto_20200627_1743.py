# Generated by Django 2.2.9 on 2020-06-27 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proglangs', '0004_auto_20200130_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compiler',
            name='language',
            field=models.CharField(blank=True, choices=[('', 'N/A'), ('c', 'C'), ('cpp', 'C++'), ('java', 'Java'), ('pas', 'Pascal'), ('dpr', 'Delphi'), ('py', 'Python'), ('cs', 'C#'), ('sh', 'Shell')], default='', max_length=8, verbose_name='language'),
        ),
    ]
