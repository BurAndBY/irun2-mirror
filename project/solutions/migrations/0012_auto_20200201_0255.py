# Generated by Django 2.2.9 on 2020-01-31 23:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0011_auto_20170505_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challengedsolution',
            name='outcome',
            field=models.IntegerField(choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed'), (11, 'Failed')], default=0),
        ),
        migrations.AlterField(
            model_name='judgement',
            name='outcome',
            field=models.IntegerField(choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed'), (11, 'Failed')], default=0),
        ),
        migrations.AlterField(
            model_name='judgementextrainfo',
            name='general_failure_message',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='judgementextrainfo',
            name='general_failure_reason',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='solution',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='solution',
            name='best_judgement',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='solutions.Judgement'),
        ),
        migrations.AlterField(
            model_name='solution',
            name='compiler',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='proglangs.Compiler'),
        ),
        migrations.AlterField(
            model_name='solution',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='problems.Problem'),
        ),
        migrations.AlterField(
            model_name='solution',
            name='source_code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='storage.FileMetadata'),
        ),
        migrations.AlterField(
            model_name='testcaseresult',
            name='outcome',
            field=models.IntegerField(choices=[(0, 'N/A'), (1, 'Accepted'), (2, 'Compilation Error'), (3, 'Wrong Answer'), (4, 'Time Limit Exceeded'), (5, 'Memory Limit Exceeded'), (6, 'Idleness Limit Exceeded'), (7, 'Run-time Error'), (8, 'Presentation Error'), (9, 'Security Violation'), (10, 'Check Failed'), (11, 'Failed')], default=0),
        ),
    ]
