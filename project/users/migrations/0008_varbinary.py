# Generated by Django 2.2.9 on 2020-02-21 00:42

from django.db import migrations

from storage.storage import ResourceIdField


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_admingroup'),
    ]

    operations = [
        migrations.AlterField('UserProfile', 'photo', ResourceIdField(null=True)),
        migrations.AlterField('UserProfile', 'photo_thumbnail', ResourceIdField(null=True)),
    ]
