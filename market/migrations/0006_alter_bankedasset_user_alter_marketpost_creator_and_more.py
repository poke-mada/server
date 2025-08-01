# Generated by Django 5.1.5 on 2025-07-28 03:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_api', '0061_remove_streamer_user'),
        ('market', '0005_markettransaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankedasset',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event_api.mastersprofile'),
        ),
        migrations.AlterField(
            model_name='marketpost',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event_api.mastersprofile'),
        ),
        migrations.AlterField(
            model_name='marketpostoffer',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event_api.mastersprofile'),
        ),
    ]
