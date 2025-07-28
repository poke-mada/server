from django.core.validators import MinValueValidator
from django.db import models


# Create your models here.
class InventoryGiftQuerySequence(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    run_times = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    inventory_bundle = models.ForeignKey('rewards_api.RewardBundle', on_delete=models.CASCADE)
    targets = models.ManyToManyField('event_api.MastersProfile')

    def run(self):
        from rewards_api.models import StreamerRewardInventory
        for target in self.targets.all():
            inventory, is_created = StreamerRewardInventory.objects.get_or_create(
                reward_id=self.inventory_bundle_id,
                profile=target, defaults=dict(
                    exchanges=0,
                    is_available=True
                ))
            if not inventory.is_available:
                inventory.is_available = True
            inventory.save()
        self.run_times += 1
        self.save()

    class Meta:
        verbose_name = 'Gift Log'
        verbose_name_plural = 'Gift Logs'


# Create your models here.
class DirectGiftQuerySequence(models.Model):
    WILDCARD = 1
    MONEY = 0
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    run_times = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    targets = models.ManyToManyField('event_api.MastersProfile')

    def run(self):
        from event_api.models import CoinTransaction, StreamerWildcardInventoryItem
        for target in self.targets.all():
            for gift in self.gifts.all():
                if gift.type == DirectGiftQuerySequence.MONEY:
                    CoinTransaction.objects.create(
                        profile=target,
                        amount=abs(gift.quantity),
                        TYPE=CoinTransaction.OUTPUT if gift.quantity < 0 else CoinTransaction.INPUT,
                        reason=f'Se entregaron {gift.quantity} usando DGL: {self.name}'
                    )
                elif gift.type == DirectGiftQuerySequence.WILDCARD:
                    item, is_created = StreamerWildcardInventoryItem.objects.get_or_create(profile=target, wildcard=gift.wildcard, defaults=dict(
                        quantity=1
                    ))
                    if not is_created:
                        item.quantity += 1
                        item.save()
        self.run_times += 1
        self.save()

    class Meta:
        verbose_name = 'Direct Gift Log'
        verbose_name_plural = 'Direct Gift Logs'


# Create your models here.
class DirectGift(models.Model):
    WILDCARD = 1
    MONEY = 0

    REWARD_TYPES = {
        WILDCARD: 'Wildcard',
        MONEY: 'Money',
    }

    type = models.SmallIntegerField(choices=REWARD_TYPES.items(), default=MONEY)
    sequence = models.ForeignKey(DirectGiftQuerySequence, on_delete=models.SET_NULL, null=True, related_name='gifts')

    wildcard = models.ForeignKey("event_api.Wildcard", on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f'{self.pk} - {self.get_type_display()}'
