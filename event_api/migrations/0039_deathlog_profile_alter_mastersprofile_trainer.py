# Generated by Django 5.1.5 on 2025-05-25 07:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_api', '0038_alter_wildcardlog_trainer'),
        ('trainer_data', '0013_remove_trainer_custom_sprite'),
    ]

    operations = [
        migrations.AddField(
            model_name='deathlog',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deaths', to='event_api.mastersprofile'),
        ),
        migrations.AlterField(
            model_name='mastersprofile',
            name='trainer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='trainer_data.trainer'),
        ),
    ]
