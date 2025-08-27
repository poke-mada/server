from django.db import models


class BankPokemon(models.Model):
    species_name = models.CharField(max_length=50)
    trainer_pokemon = models.ForeignKey('trainer_data.TrainerPokemon', on_delete=models.SET_NULL, null=True)
    enc_data = models.FileField(null=True, blank=False)


    def save(self, *args, **kwargs):

        return super().save(*args, **kwargs)


class MarketBank(models.Model):
    pass
