# Generated by Django 3.1.2 on 2021-12-02 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0014_auto_20211029_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='scoring_policy',
            field=models.IntegerField(choices=[(0, 'Auto'), (1, 'Take last solution'), (2, 'Take best solution')], default=0, verbose_name='scoring policy'),
        ),
    ]
