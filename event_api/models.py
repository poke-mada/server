from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from pokemon_api.scripting.save_reader import clamp
from trainer_data.models import Trainer


# Create your models here.
class SaveFile(models.Model):
    accessible = models.BooleanField(default=False)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='saves')
    file = models.FileField(upload_to='saves/')
    created_on = models.DateTimeField(auto_now_add=True, null=True)


class ErrorLog(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    details = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=False)


class CoinTransaction(models.Model):
    INPUT = 0
    OUTPUT = 1
    TRANSACTION_TYPES = (
        (INPUT, 'Ingreso'),
        (OUTPUT, 'Egreso')
    )
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    reason = models.TextField(blank=False, default="No reason provided")
    TYPE = models.SmallIntegerField(choices=TRANSACTION_TYPES, default=INPUT)

    class Meta:
        verbose_name = 'Economy Log'
        verbose_name_plural = 'Economy Logs'


class Wildcard(models.Model):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2
    LEGENDARY = 3

    QUALITIES = (
        (COMMON, 'Common'),
        (UNCOMMON, 'Uncommon'),
        (RARE, 'Rare'),
        (LEGENDARY, 'Legendary'),
    )

    name = models.CharField(max_length=500)
    price = models.IntegerField(validators=[MinValueValidator(-1)], null=True, blank=True)
    special_price = models.CharField(max_length=500, null=True, blank=True)
    sprite = models.ImageField(upload_to='wildcards/', null=True, blank=True)
    description = models.TextField(blank=False, default="")
    quality = models.SmallIntegerField(choices=QUALITIES, default=COMMON)
    is_active = models.BooleanField(default=True)
    extra_url = models.URLField(blank=True, null=True)
    always_available = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def sprite_name(self):
        return self.sprite.name

    def can_buy(self, trainer, amount, force_buy=False):
        streamer = trainer.get_streamer()
        inventory, _ = streamer.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        already_in_possession = inventory.quantity
        if not force_buy:
            amount_to_buy = clamp(amount - already_in_possession, 0)
        else:
            amount_to_buy = amount
        return self.is_active and ((trainer.economy >= self.price * amount_to_buy) or self.always_available)

    def can_use(self, trainer, amount):
        streamer = trainer.get_streamer()
        inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=self).first()
        return (inventory and inventory.quantity >= amount) or self.always_available

    def buy(self, trainer, amount: int, force_buy=False):
        streamer = trainer.get_streamer()
        if not self.is_active:
            return False
        if self.always_available:
            return True
        inventory, _ = streamer.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        already_in_possession = inventory.quantity
        if not force_buy:
            amount_to_buy = clamp(amount - already_in_possession, 0)
        else:
            amount_to_buy = amount

        CoinTransaction.objects.create(
            trainer=trainer,
            amount=self.price * amount_to_buy,
            TYPE=CoinTransaction.OUTPUT,
            reason=f'se compró la carta {self.name}'
        )

        inventory.quantity += amount_to_buy
        inventory.save()
        return amount_to_buy

    def use(self, trainer, amount: int):
        streamer = trainer.get_streamer()
        match self.id:
            case 6:
                CoinTransaction.objects.create(
                    trainer=trainer,
                    amount=3 * amount,
                    TYPE=CoinTransaction.INPUT,
                    reason=f'se uso la carta {self.name} {amount} veces'
                )
                WildcardLog.objects.create(wildcard=self, trainer=trainer,
                                           details=f'{amount} carta/s {self.name} usada')
                return True
            case 37:
                CoinTransaction.objects.create(
                    trainer=trainer,
                    amount=4 * amount,
                    TYPE=CoinTransaction.INPUT,
                    reason=f'se uso la carta {self.name} {amount} veces'
                )
                WildcardLog.objects.create(wildcard=self, trainer=trainer,
                                           details=f'{amount} carta/s {self.name} usada')
            case _:
                try:
                    WildcardLog.objects.create(wildcard=self, trainer=trainer,
                                               details=f'{amount} carta/s {self.name} usada')
                except Exception as e:
                    ErrorLog.objects.create(trainer=trainer, details=f'{amount} cartas {self.name} intentaron usarse',
                                            message=str(e))
                    raise e

        inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=self).first()
        inventory.quantity -= amount
        inventory.save()
        return True


class WildcardLog(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='use_logs')
    wildcard = models.ForeignKey(Wildcard, on_delete=models.CASCADE, related_name='use_logs')
    details = models.TextField(blank=False, default="No details provided")


class StreamPlatformUrl(models.Model):
    streamer = models.ForeignKey("Streamer", on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    url = models.URLField()

    def __str__(self):
        return self.platform


class StreamerWildcardInventoryItem(models.Model):
    streamer = models.ForeignKey("Streamer", on_delete=models.CASCADE, related_name='wildcard_inventory')
    wildcard = models.ForeignKey(Wildcard, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'x{self.quantity} {self.wildcard.name}'


class Streamer(models.Model):
    name = models.CharField(max_length=50, default="")

    def __str__(self):
        return self.name


class CoachProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="coaching_profile")
    coached_trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="coaches", null=True,
                                        blank=True)

    def __str__(self):
        return self.user.username


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="trainer_profile")
    trainer = models.OneToOneField(Trainer, on_delete=models.PROTECT, related_name="user", null=True, blank=True)

    def __str__(self):
        return self.user.username


class LoaderThread(models.Model):
    thread_id = models.CharField(max_length=100, default="", blank=True)


class GameMod(models.Model):
    mod_file = models.FileField(upload_to='mods/', null=False)
    mod_name = models.CharField(max_length=50, blank=False)
    mod_description = models.TextField(blank=True, null=True)

    def get_mod_file_for_streamer(self, streamer):
        streamer_variant = self.variants.filter(streamer=streamer).first()
        if streamer_variant:
            return streamer_variant.mod_file

        return self.mod_file


class StreamerGameMod(models.Model):
    streamer = models.ForeignKey(Streamer, on_delete=models.CASCADE, related_name="mods")
    game_mod = models.ForeignKey(GameMod, on_delete=models.CASCADE, related_name="variants")
    mod_file = models.FileField(upload_to='mods/streamer/', null=False)


class GameEvent(models.Model):
    game_mod = models.ForeignKey(GameMod, on_delete=models.PROTECT, related_name="events")
    available_date_from = models.DateTimeField()
    available_date_to = models.DateTimeField()
    force_available = models.BooleanField()

    def is_available(self):
        if self.force_available:
            return True
        now_time = datetime.now()
        return self.available_date_from <= now_time <= self.available_date_to

    @staticmethod
    def get_available():
        now_time = datetime.now()
        return Q(force_available=True) | Q(available_date_from__gte=now_time, available_date_to__lte=now_time)
