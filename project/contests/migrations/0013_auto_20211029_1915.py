# Generated by Django 3.1.2 on 2021-10-29 16:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0012_auto_20200627_1745'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contest',
            old_name='attempt_limit',
            new_name='total_attempt_limit',
        ),
    ]
