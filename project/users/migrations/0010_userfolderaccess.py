# Generated by Django 2.2.9 on 2020-04-12 22:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0009_userprofile_has_access_to_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFolderAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.IntegerField(choices=[(1, 'Read'), (2, 'Write')])),
                ('when_granted', models.DateTimeField(auto_now=True)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.UserFolder')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='users.AdminGroup')),
                ('who_granted', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('folder', 'group')},
            },
        ),
    ]
