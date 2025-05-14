import os
from typing import Union

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.safestring import mark_safe

from pokemon_api.models import Pokemon, Move, PokemonNature, Type, Item, PokemonAbility


# Create your models here.


class Trainer(models.Model):
    streamer = models.OneToOneField("event_api.Streamer", on_delete=models.CASCADE, related_name="trainer", null=True)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=50, db_index=True, unique=True)
    custom_sprite = models.ImageField(upload_to='trainers/sprites/', null=True, blank=True)
    current_team = models.ForeignKey("TrainerTeam", on_delete=models.CASCADE, related_name='trainer', null=True,
                                     blank=True)

    def streamer_name(self):
        if not self.streamer:
            return f'T - {self.name}'
        return self.streamer.name

    def get_streamer(self):
        return self.user.streamer

    def __str__(self):
        return self.streamer_name() or self.name

    @classmethod
    def get_from_user(cls, user) -> Union["Trainer", None]:
        from event_api.models import MastersProfile
        if user.masters_profile:
            if user.masters_profile.profile_type != MastersProfile.ADMIN:
                return user.masters_profile.trainer
        return None


class TrainerPokemon(models.Model):
    team = models.ForeignKey("TrainerTeam", related_name='team', on_delete=models.CASCADE, null=True)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.PROTECT, related_name='trainereds')
    mote = models.CharField(max_length=15)
    form = models.CharField(max_length=50, default='0', null=True, blank=True)
    moves = models.ManyToManyField(Move, blank=True)
    types = models.ManyToManyField(Type, blank=True)
    held_item = models.ForeignKey(Item, on_delete=models.PROTECT)
    ability = models.ForeignKey(PokemonAbility, on_delete=models.PROTECT, related_name='pokemons')
    mega_ability = models.ForeignKey(PokemonAbility, on_delete=models.SET_NULL, null=True, blank=True, related_name='megas')
    nature = models.ForeignKey(PokemonNature, on_delete=models.PROTECT)
    level = models.IntegerField(default=1, validators=[MaxValueValidator(100), MinValueValidator(1)])
    suffix = models.CharField(max_length=50, default='', null=True, blank=True)
    cur_hp = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    max_hp = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    speed = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    special_attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    special_defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_hp = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_speed = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_special_attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    ev_special_defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_hp = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_speed = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_special_attack = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)
    iv_special_defense = models.IntegerField(default=1, validators=[MinValueValidator(0)], null=True)

    def __str__(self):
        return self.mote


class TrainerTeam(models.Model):
    version = models.IntegerField()
    trainer_old = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='old_teams', null=True, blank=True)

    def __str__(self):
        return f'{self.trainer_old.name}\'s team #{self.version}'

    def pokemon_team(self):
        motes = self.team.values_list('mote')
        return motes


class TrainerBox(models.Model):
    id = models.AutoField(primary_key=True)
    box_number = models.IntegerField(db_index=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='boxes')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name or f'Box #{self.box_number}'

    class Meta:
        verbose_name_plural = "Trainer Boxes"


class TrainerBoxSlot(models.Model):
    slot = models.IntegerField()
    pokemon = models.ForeignKey(TrainerPokemon, on_delete=models.CASCADE, null=True, blank=True)
    box = models.ForeignKey(TrainerBox, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)

    def __str__(self):
        return f'Slot #{self.slot}'
