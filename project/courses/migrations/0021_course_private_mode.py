# Generated by Django 3.1.2 on 2021-09-11 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0020_auto_20200706_0243'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='private_mode',
            field=models.BooleanField(blank=True, default=False, verbose_name='private mode: student names are hidden'),
        ),
    ]
