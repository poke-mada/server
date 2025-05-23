# Generated by Django 5.1.5 on 2025-01-20 08:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainer_data', '0003_trainer_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainerbox',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='trainerbox',
            name='trainer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boxes', to='trainer_data.trainer'),
        ),
        migrations.AlterField(
            model_name='trainerboxslot',
            name='box',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='trainer_data.trainerbox'),
        ),
        migrations.AlterField(
            model_name='trainerboxslot',
            name='pokemon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='trainer_data.trainerpokemon'),
        ),
    ]
