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

    pokemon_pid = models.PositiveBigIntegerField(blank=True, null=True)
    pokemon_data = models.FileField(upload_to='pokemon_rewards', null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], null=True, blank=True)

    def __str__(self):
        return f'{self.pk} - {self.get_reward_type_display()}'

    def save(self, *args, **kwargs):
        if self.reward_type == Reward.POKEMON and self.pokemon_data:
            from pokemon_api.scripting.save_reader import PokemonBytes
            import struct
            pokemon = PokemonBytes(self.pokemon_data.read())
            self.pokemon_pid = struct.unpack("<I", pokemon.raw_data[0x18:0x1C])[0]
            print(self.pokemon_pid)
        super().save(*args, **kwargs)


class StreamerRewardInventory(models.Model):
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, related_name='reward_inventory',
                                null=True, blank=False)
    reward = models.ForeignKey(RewardBundle, on_delete=models.SET_NULL, null=True, related_name='owners')
    exchanges = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['reward', 'profile']
