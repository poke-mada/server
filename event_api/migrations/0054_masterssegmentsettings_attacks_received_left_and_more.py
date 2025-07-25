# Generated by Django 5.1.5 on 2025-07-24 06:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_api', '0053_remove_cointransaction_trainer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='attacks_received_left',
            field=models.DecimalField(decimal_places=1, default=4, help_text='Ataques que puede recibir en el tramo', max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)], verbose_name='Experiencia'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='cure_lady_left',
            field=models.IntegerField(default=1, help_text='Cuantos comodines de Dama de la Cura quedan en el tramo', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)], verbose_name='Dama de la Cura restantes'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='death_count',
            field=models.IntegerField(default=0, help_text='Muertes en un tramo', validators=[django.core.validators.MinValueValidator(0)], verbose_name='Conteo de muertes'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='karma',
            field=models.DecimalField(decimal_places=1, default=1, help_text='Capacidad de usar comodines de ataque fuerte', max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)], verbose_name='Karma'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='shinies_freed',
            field=models.IntegerField(default=0, help_text='Cuantos shinies ha liberado en el tramo', validators=[django.core.validators.MinValueValidator(0)], verbose_name='Shinies liberados'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='steal_karma',
            field=models.DecimalField(decimal_places=1, default=0, help_text='Al juntar 3, se desbloquea "Robo justo"', max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)], verbose_name='Karma de Robo Justo'),
        ),
        migrations.AddField(
            model_name='masterssegmentsettings',
            name='tournament_league',
            field=models.CharField(choices=[('-', '------'), ('A', 'Liga A'), ('B', 'Liga B'), ('C', 'Liga C'), ('D', 'Liga D'), ('E', 'Liga E')], default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='masterssegmentsettings',
            name='community_pokemon_id',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(821)], verbose_name='Pokemon de comunidad'),
        ),
    ]
