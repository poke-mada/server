# Generated by Django 5.1.5 on 2025-07-05 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_api', '0045_mastersprofile_tournament_league_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mastersprofile',
            name='web_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/web/'),
        ),
    ]
