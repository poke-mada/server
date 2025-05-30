# Generated by Django 5.1.5 on 2025-03-25 01:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards_api', '0004_streamerrewardinventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemreward',
            name='bag',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='streamerrewardinventory',
            name='reward',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owners', to='rewards_api.rewardbundle'),
        ),
    ]
