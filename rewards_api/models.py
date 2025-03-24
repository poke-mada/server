import uuid

from django.core.validators import MinValueValidator
from django.db import models

from event_api.models import Streamer
from pokemon_api.models import Item, Pokemon
from trainer_data.models import TrainerPokemon


class RewardBundle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Create your models here.
class Reward(models.Model):
    ITEM = 0
    WILDCARD = 1
    MONEY = 2
    POKEMON = 3

    REWARD_TYPES = {
        ITEM: 'Item',
        WILDCARD: 'Wildcard',
        MONEY: 'Money',
        POKEMON: 'Pokemon'
    }

    reward_type = models.SmallIntegerField(choices=REWARD_TYPES.items(), default=MONEY)
    is_active = models.BooleanField(default=True)
    bundle = models.ForeignKey(RewardBundle, on_delete=models.SET_NULL, null=True, related_name='rewards')

    def get_reward(self):
        match self.reward_type:
            case self.ITEM:
                return self.item_reward
            case self.WILDCARD:
                return self.wildcard_reward
            case self.MONEY:
                return self.money_reward
            case self.POKEMON:
                return self.pokemon_reward

    def __str__(self):
        return f'{self.pk} - {self.get_reward_type_display()}'


class PokemonReward(models.Model):
    reward = models.OneToOneField(Reward, on_delete=models.SET_NULL, null=True, related_name='pokemon_reward',
                                  blank=True)
    pokemon_data = models.FileField(upload_to='pokemon_rewards')
    pokemon_pid = models.PositiveIntegerField(db_index=True, unique=True)
    pokemon = models.ForeignKey(TrainerPokemon, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pokemon:
            from pokemon_api.scripting.save_reader import PokemonBytes
            pokemon = PokemonBytes(self.pokemon_data.read())
            pokemon.get_atts()
            trained_pokemon = pokemon.to_trained_pokemon()
            self.pokemon = trained_pokemon
        super().save(*args, **kwargs)

    def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):
        super().full_clean(exclude, validate_unique, validate_constraints)
        # TODO: validate pokemon data to be coherent


class ItemReward(models.Model):
    reward = models.OneToOneField(Reward, on_delete=models.SET_NULL, null=True, related_name='item_reward')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])


class WildcardReward(models.Model):
    reward = models.OneToOneField(Reward, on_delete=models.SET_NULL, null=True, related_name='wildcard_reward')
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])


class MoneyReward(models.Model):
    reward = models.OneToOneField(Reward, on_delete=models.SET_NULL, null=True, related_name='money_reward')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])


class StreamerRewardInventory(models.Model):
    reward = models.ForeignKey(RewardBundle, on_delete=models.SET_NULL, null=True)
    streamer = models.ForeignKey(Streamer, on_delete=models.SET_NULL, null=True, related_name='rewards')
    exchanges = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['reward', 'streamer']
