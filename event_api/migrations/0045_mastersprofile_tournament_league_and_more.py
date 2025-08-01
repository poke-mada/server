# Generated by Django 5.1.5 on 2025-07-05 21:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_api', '0044_imposter_profileimposterlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastersprofile',
            name='tournament_league',
            field=models.CharField(choices=[('A', 'Liga A'), ('B', 'Liga B'), ('C', 'Liga C'), ('D', 'Liga D'), ('E', 'Liga E')], default='A', max_length=1),
        ),
        migrations.AddField(
            model_name='mastersprofile',
            name='web_picture',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='profiles/web/'),
        ),
        migrations.AlterField(
            model_name='masterssegmentsettings',
            name='segment',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(99)], verbose_name='Tramo'),
        ),
    ]
