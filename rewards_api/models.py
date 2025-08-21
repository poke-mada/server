import uuid

from django.core.validators import MinValueValidator
from django.db import models

from pokemon_api.models import Item, Pokemon
from trainer_data.models import TrainerPokemon


class RewardBundle(models.Model):
    REWARD_BUNDLE = 0
    ROULETTE_BUNDLE = 1
    WILDCARD_BUNDLE = 2

    BUNDLE_TYPES = {
        REWARD_BUNDLE: 'Premio',
        ROULETTE_BUNDLE: 'Ruleta',
        WILDCARD_BUNDLE: 'Comodin'
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user_created = models.BooleanField(default=False)
    sender = models.CharField(max_length=50, null=True, default='Evento')
    type = models.SmallIntegerField(choices=BUNDLE_TYPES.items(), default=REWARD_BUNDLE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Preset De Inventario"
        verbose_name_plural = "Presets de Inventario"


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

    class Meta:
        verbose_name = "Elemento del Inventario"
        verbose_name_plural = "Elementos del Inventario"


class StreamerRewardInventory(models.Model):
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, related_name='reward_inventory',
                                null=True, blank=False)
    reward = models.ForeignKey(RewardBundle, on_delete=models.SET_NULL, null=True, related_name='owners')
    exchanges = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['reward', 'profile']


class Roulette(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=500, null=True, blank=True)
    file = models.FileField(upload_to='ruletas/', null=True, blank=True)
    recreate_at_save = models.BooleanField(default=False, verbose_name="Recrear al guardar")
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Comodin Asignada", help_text="Comodin usado para validar tiradas")
    banner_image = models.ImageField(upload_to='banners/', null=True, blank=False, help_text="Imagen grande del Banner")
    banner_logo = models.ImageField(upload_to='banners/', null=True, blank=False, help_text="Logo chico del banner")

    def save(self, *args, **kwargs):
        if self.recreate_at_save:
            from event_api.models import Wildcard
            super().save(*args, **kwargs)
            self.prices.all().delete()
            lines = self.file.readlines()
            for line in lines[1:]:
                clean_line: str = line.strip().decode()
                splitted = clean_line.split(' (x')
                wildcard_name = splitted[0]
                try:
                    quantity = splitted[1]
                except:
                    quantity = '1'
                quantity = int(quantity.replace(')', ''))
                RoulettePrice.objects.create(
                    name=clean_line,
                    wildcard=Wildcard.objects.filter(name__iexact=wildcard_name.lower()).first(),
                    quantity=quantity,
                    roulette=self
                )
            self.recreate_at_save = False
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ruleta"
        verbose_name_plural = "Ruletas"


class RoulettePrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    roulette = models.ForeignKey(Roulette, related_name='prices', on_delete=models.CASCADE)
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.PROTECT, verbose_name='Comodin', null=True, blank=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Cantidad')

    class Meta:
        verbose_name = "Premio de Ruleta"
        verbose_name_plural = "Premios de Ruleta"