# Generated by Django 2.2.9 on 2020-05-07 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_auto_20200507_0345'),
    ]

    operations = [
        migrations.AddField(
            model_name='icpccoach',
            name='is_confirmed',
            field=models.BooleanField(blank=True, default=True, verbose_name='Confirmed'),
        ),
    ]
