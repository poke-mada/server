from django.db import models

from websocket.sockets import DataConsumer


# Create your models here.
class InventoryGiftQuerySequence(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    run_times = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    inventory_bundle = models.ForeignKey('rewards_api.RewardBundle', on_delete=models.CASCADE)
    targets = models.ManyToManyField('event_api.MastersProfile', null=True, blank=True)
    give_all = models.BooleanField(default=False)

    def run(self):
        from event_api.models import MastersProfile
        from rewards_api.models import StreamerRewardInventory
        if self.give_all:
            for target in MastersProfile.objects.all():
                inventory, is_created = StreamerRewardInventory.objects.get_or_create(
                    reward_id=self.inventory_bundle_id,
                    profile=target, defaults=dict(
                        exchanges=0,
                        is_available=True
                    ))

                DataConsumer.send_custom_data(target.user.username, dict(
                    type='notification',
                    data='Te ha llegado un paquete al buzón!'
                ))
                if not inventory.is_available:
                    inventory.is_available = True
                inventory.save()
        else:
            for target in self.targets.all():
                inventory, is_created = StreamerRewardInventory.objects.get_or_create(
                    reward_id=self.inventory_bundle_id,
                    profile=target, defaults=dict(
                        exchanges=0,
                        is_available=True
                    ))

                DataConsumer.send_custom_data(target.user.username, dict(
                    type='notification',
                    data='Te ha llegado un paquete al buzón!'
                ))
                if not inventory.is_available:
                    inventory.is_available = True
                inventory.save()

        self.run_times += 1
        self.save()

    class Meta:
        verbose_name = 'Envío de Preset al Buzón'
        verbose_name_plural = 'Envío de Presets al Buzón'


class ShowdownToken(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    token = models.CharField(max_length=200)

    def __str__(self):
        return self.username


# Create your models here.
class DirectGiftQuerySequence(models.Model):
    WILDCARD = 1
    MONEY = 0
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    run_times = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    targets = models.ManyToManyField('event_api.MastersProfile', null=True, blank=True)
    give_all = models.BooleanField(default=False)

    def run(self):
        from event_api.models import MastersProfile
        from event_api.models import CoinTransaction, StreamerWildcardInventoryItem
        if self.give_all:
            for target in MastersProfile.objects.all():
                for gift in self.gifts.all():
                    if gift.type == DirectGiftQuerySequence.MONEY:
                        CoinTransaction.objects.create(
                            profile=target,
                            amount=abs(gift.quantity),
                            TYPE=CoinTransaction.OUTPUT if gift.quantity < 0 else CoinTransaction.INPUT,
                            reason=f'Se entregaron {gift.quantity} usando DGL: {self.name}'
                        )
                    elif gift.type == DirectGiftQuerySequence.WILDCARD:
                        item, is_created = StreamerWildcardInventoryItem.objects.get_or_create(profile=target,
                                                                                               wildcard=gift.wildcard,
                                                                                               defaults=dict(
                                                                                                   quantity=gift.quantity
                                                                                               ))
                        if not is_created:
                            item.quantity += gift.quantity
                            item.save()
        else:
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
                        item, is_created = StreamerWildcardInventoryItem.objects.get_or_create(profile=target,
                                                                                               wildcard=gift.wildcard,
                                                                                               defaults=dict(
                                                                                                   quantity=gift.quantity
                                                                                               ))
                        if not is_created:
                            item.quantity += gift.quantity
                            item.save()
        self.run_times += 1
        self.save()

    class Meta:
        verbose_name = 'Correccion Directa'
        verbose_name_plural = 'Correcciones Directas'


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


class BanPokemonSequence(models.Model):
    profile = models.ForeignKey("event_api.MastersProfile", on_delete=models.CASCADE)
    dex_number = models.IntegerField()
    reason = models.TextField(blank=True)
    run_on_save = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.run_on_save:
            from pokemon_api.models import Pokemon
            from event_api.models import BannedPokemon
            banned_mon = Pokemon.objects.filter(dex_number=self.dex_number).first()
            banned_forms = banned_mon.surrogate()
            for pokemon in banned_forms:
                BannedPokemon.objects.create(
                    dex_number=pokemon.dex_number,
                    profile=self.profile,
                    species_name=pokemon.name,
                    reason=self.reason
                )
        return super(BanPokemonSequence, self).save(*args, **kwargs)