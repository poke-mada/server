# Generated by Django 5.1.5 on 2025-01-20 09:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trainer_data', '0004_alter_trainerbox_id_alter_trainerbox_trainer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trainer',
            name='streamer_name',
        ),
    ]
