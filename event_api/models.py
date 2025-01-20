from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from trainer_data.models import Trainer


# Create your models here.
class SaveFile(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='saves')
    file = models.FileField(upload_to='saves/')
    created_on = models.DateTimeField(auto_now_add=True, null=True)


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

    def __str__(self):
        return self.name


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
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="streamer")
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
