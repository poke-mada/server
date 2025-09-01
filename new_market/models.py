import uuid
from django.core.validators import MinValueValidator
from django.db import models


class MarketRoom(models.Model):
    id = models.UUIDField(primary_key=True, verbose_name='ID', default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey("event_api.MastersProfile", on_delete=models.SET_NULL, null=True,
                              related_name="rooms_owned")
    created_at = models.DateTimeField(auto_now_add=True)
    second_part = models.ForeignKey("event_api.MastersProfile", on_delete=models.SET_NULL, null=True,
                                    related_name="rooms_joined")
    is_active = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)


class BankPokemon(models.Model):
    owner = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, null=True,
                              related_name="banked_pokemons")
    species_name = models.CharField(max_length=50)
    trainer_pokemon = models.ForeignKey('trainer_data.TrainerPokemon', on_delete=models.SET_NULL, null=True)
    enc_data = models.FileField(null=True, blank=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            pokemon = self.trainer_pokemon
            pokemon.pk = None
            pokemon.trainer_id = None
            pokemon.save()
            self.enc_data = pokemon.enc_data
            self.species_name = pokemon.pokemon.name

        return super().save(*args, **kwargs)


class BankItem(models.Model):
    owner = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, null=True,
                              related_name="banked_items")
    item_name = models.CharField(max_length=50)
    item = models.ForeignKey('pokemon_api.Item', on_delete=models.PROTECT, null=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        if not self.pk:
            self.item_name = self.item.name_localizations.filter(language='es').first().content
        return super().save(*args, **kwargs)


class BankWildcard(models.Model):
    owner = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE, null=True, related_name="banked_wildcards")
    wildcard = models.ForeignKey('event_api.Wildcard', on_delete=models.PROTECT, null=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])


class MarketOffer(models.Model):
    pokemon = models.ForeignKey(BankPokemon, on_delete=models.PROTECT, null=True)
    items = models.ManyToManyField(BankItem)
    wildcards = models.ManyToManyField(BankWildcard)


class MarketBlockLog(models.Model):
    dex_number = models.IntegerField(null=True)
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.SET_NULL, null=True)
    blocked_until = models.DateTimeField()


class MarketCooldownLog(models.Model):
    dex_number = models.IntegerField(null=True)
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.SET_NULL, null=True)
    blocked_until = models.DateTimeField()
