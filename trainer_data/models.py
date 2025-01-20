import os

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.safestring import mark_safe

from pokemon_api.models import Pokemon, Move, PokemonNature, Type, Item, PokemonAbility


# Create your models here.


class Trainer(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=50, db_index=True, unique=True)
    custom_sprite = models.ImageField(upload_to='trainers/sprites/', null=True, blank=True)
    current_team = models.ForeignKey("TrainerTeam", on_delete=models.PROTECT, related_name='trainer', null=True,
                                     blank=True)

    @property
    def last_save(self):
        return self.saves.order_by('created_on').last().file.url

    @property
    def economy(self):
        from event_api.models import CoinTransaction
        inputs = self.transactions.filter(TYPE=CoinTransaction.INPUT).aggregate(Sum('amount'))['amount__sum'] or 0
        outputs = self.transactions.filter(TYPE=CoinTransaction.OUTPUT).aggregate(Sum('amount'))['amount__sum'] or 0
        return inputs - outputs

    def last_save_download(self):
        return mark_safe('<a href="{0}" download>Download {1} Save</a>'.format(self.last_save, self.name))

    def streamer_name(self):
        if not self.streamer:
            print('awa')
            return None
        return self.streamer.name

    def __str__(self):
        return self.streamer_name() or self.name


class TrainerPokemon(models.Model):
    team = models.ForeignKey("TrainerTeam", related_name='team', on_delete=models.CASCADE, null=True)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.PROTECT, related_name='trainereds')
    mote = models.CharField(max_length=15)
    form = models.CharField(max_length=50, default='0', null=True, blank=True)

    notes = models.TextField(default='', blank=True)

    moves = models.ManyToManyField(Move, blank=True)
    types = models.ManyToManyField(Type, blank=True)

    held_item = models.ForeignKey(Item, on_delete=models.PROTECT)
    ability = models.ForeignKey(PokemonAbility, on_delete=models.PROTECT)
    nature = models.ForeignKey(PokemonNature, on_delete=models.PROTECT)
    level = models.IntegerField(default=1, validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])

    cur_hp = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    max_hp = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    attack = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    defense = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    speed = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    special_attack = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)
    special_defense = models.IntegerField(default=1, validators=[
        MinValueValidator(0)
    ], null=True)

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

    class Meta:
        verbose_name_plural = "Trainer Boxes"


class TrainerBoxSlot(models.Model):
    slot = models.IntegerField()
    pokemon = models.ForeignKey(TrainerPokemon, on_delete=models.CASCADE, null=True, blank=True)
    box = models.ForeignKey(TrainerBox, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
