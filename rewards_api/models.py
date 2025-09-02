import json
import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum, Window, F

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
    name = models.CharField(max_length=100, null=True)
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
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Comodin Asignada", help_text="Comodin usado para validar tiradas")
    banner_image = models.ImageField(upload_to='banners/', null=True, blank=False, help_text="Imagen grande del Banner")
    banner_logo = models.ImageField(upload_to='banners/', null=True, blank=False, help_text="Logo chico del banner")
    active_banner_logo = models.ImageField(upload_to='banners/', null=True, blank=False,
                                           help_text="Logo chico del banner activo")
    order = models.IntegerField(verbose_name='Orden vertical', default=0)
    segment = models.IntegerField(verbose_name="Tramo Para Aparecer",
                                  validators=[MinValueValidator(1), MaxValueValidator(8)], default=1)

    def save(self, *args, **kwargs):
        if self.recreate_at_save:
            from event_api.models import Wildcard
            self.prices.all().delete()

            data = self.file.read()
            json_data = json.loads(data)
            self.name = json_data['name']
            for price in json_data['prices']:
                wildcard_f_obj = Wildcard.objects.filter(name__iexact=price['wildcards'][0]['name'].lower()).first()
                price_obj = RoulettePrice.objects.create(
                    name=price['name'],
                    is_jackpot=price.get('is_jackpot', False),
                    roulette=self,
                    weight=price.get('weight')
                )
                if wildcard_f_obj:
                    price_obj.image = wildcard_f_obj.sprite
                    price_obj.save()
                for wildcard in price['wildcards']:
                    wildcard_obj = Wildcard.objects.filter(name__iexact=wildcard['name'].lower()).first()
                    RoulettePriceWildcard.objects.create(
                        price=price_obj,
                        wildcard=wildcard_obj,
                        quantity=wildcard['quantity']
                    )
            self.recreate_at_save = False
        return super().save(*args, **kwargs)

    def spin(self):
        """
        Selecciona un premio con 1 ida a la DB usando window functions.
        PostgreSQL requerido.
        """
        qs = self.prices.filter(weight__gt=0)

        # Si no hay filas con peso, falla antes:
        if not qs.exists():
            raise ValueError("La ruleta no tiene premios con weight > 0")

        # 1) Obtener el total de pesos (agregación pequeña)
        total = qs.aggregate(total=Sum('weight'))['total']
        if total is None or total <= 0:
            raise ValueError("La ruleta no tiene pesos positivos")

        # 2) Generar r en Python (también podrías usar funciones SQL si quisieras)
        import random
        r = random.uniform(0, total)

        # 3) Anotar el acumulado (orden estable: por id, o por created_at si tienes)
        annotated = qs.annotate(
            cum_weight=Window(
                expression=Sum('weight'),
                order_by=F('id').asc(),  # elige un orden estable
            )
        ).filter(cum_weight__gte=r).order_by('cum_weight')

        # 4) Tomar el primero
        return annotated.first()

    class Meta:
        verbose_name = "Ruleta"
        verbose_name_plural = "Ruletas"

    def __str__(self):
        return self.name


class RoulettePrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    roulette = models.ForeignKey(Roulette, related_name='prices', on_delete=models.CASCADE)
    is_jackpot = models.BooleanField(default=False)
    image = models.ImageField(upload_to='roulette/images/', blank=True, null=True)
    weight = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Premio de Ruleta"
        verbose_name_plural = "Premios de Ruleta"

    def __str__(self):
        return self.name


class RoulettePriceWildcard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.ForeignKey(RoulettePrice, related_name='wildcards', on_delete=models.CASCADE)
    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.PROTECT, verbose_name='Comodin', null=True,
                                 blank=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Cantidad')

    class Meta:
        verbose_name = "Comodin de Premio"
        verbose_name_plural = "Comodines de Premios"


class RouletteRollHistory(models.Model):
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, related_name='roulette_hiistory',
                                verbose_name="perfil")
    roulette = models.ForeignKey(Roulette, related_name='history', on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Ruleta')
    message = models.CharField(max_length=500, verbose_name='Mensaje de Display')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Tirada')

    class Meta:
        verbose_name = "Hitoria de Ruleta"
        verbose_name_plural = "Historial de tiradas de Ruleta"
