# models.py
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from pokemon_api.models import Item


class GiveItemHandlerSettings(models.Model):
    ITEM_BAGS = [
        ('berries', 'berries bag'),
        ('meds', 'meds bag'),
        ('tms', 'tms bag'),
        ('keys', 'keys bag'),
        ('items', 'items bag')
    ]
    wildcard = models.OneToOneField('Wildcard', on_delete=models.CASCADE, related_name="give_item_settings", blank=True)
    item_id = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="give_item_wildcard", blank=True)
    item_bag = models.CharField(max_length=100, null=True, blank=True, choices=ITEM_BAGS)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(999)], blank=True)

    def __str__(self):
        return str(self.wildcard)


class GiveMoneyHandlerSettings(models.Model):
    wildcard = models.OneToOneField('Wildcard', on_delete=models.CASCADE, related_name="give_money_settings",
                                    blank=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(999)], blank=True)

    def __str__(self):
        return str(self.wildcard)


class GiveGameMoneyHandlerSettings(models.Model):
    wildcard = models.OneToOneField('Wildcard', on_delete=models.CASCADE, related_name="give_game_money_settings",
                                    blank=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(1000000)], blank=True)

    def __str__(self):
        return str(self.wildcard)
