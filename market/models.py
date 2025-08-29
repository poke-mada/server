# models.py
import abc

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum, QuerySet

from event_api.models import CoinTransaction, MastersProfile
from pokemon_api.models import Pokemon


class MarketAlert(models.Model):
    description = models.TextField(blank=False, null=True, help_text="pero que ha pasado acho")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class BankedAsset(models.Model):
    CONTENT_TYPES_LIMIT = (
            Q(app_label='pokemon_api', model='item') |
            Q(app_label='trainer_data', model='trainerpokemon')
    )
    user = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name='banked_assets')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=CONTENT_TYPES_LIMIT)
    object_id = models.PositiveIntegerField()

    object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)

    timestamp = models.DateTimeField(auto_now_add=True)
    origin = models.CharField(max_length=50, blank=True, null=True)  # Ej: "game", "market", etc.

    trade_locked = models.BooleanField(default=False)  # para evitar intercambios maliciosos

    @property
    def virtual_quantity(self):
        return self.quantity - (self.marketed.filter(post__status__in=[1, 0])
                                .aggregate(Sum('quantity'))['quantity__sum'] or 0)

    def __str__(self):
        return f'{self.content_type.name} - {self.object_id} - {self.virtual_quantity}'

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.trade_locked = True
        elif self.quantity < 0:
            self.trade_locked = True
            MarketAlert.objects.create(description=f'OBJETO CON CANTIDAD BAJO CERO!!!! BankedAsset - {self.id}')
        super(BankedAsset, self).save(*args, **kwargs)


class MarketTransactor(object):
    __slots__ = ['creator', 'items']

    def perform_transaction(self, target: MastersProfile, force_transaction=False, transaction_id=None, post_id=None):
        return


class MarketPost(models.Model, MarketTransactor):
    DRAFT = 0
    OPEN = 1
    CLOSED = 2
    CANCELLED = 3

    STATUSES = {
        DRAFT: 'Borrador',
        OPEN: 'Abierto',
        CLOSED: 'Cerrado',
        CANCELLED: 'Cancelado',
    }
    creator = models.ForeignKey(MastersProfile, on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=STATUSES.items(), default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    already_closed = models.BooleanField(default=False)
    selected_offer = models.ForeignKey("MarketPostOffer", null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return f'POST {self.id}|{self.creator}'


class MarketPostOffer(models.Model, MarketTransactor):
    DRAFT = 0
    OPEN = 1
    CLOSED = 2
    CANCELLED = 3

    STATUSES = {
        DRAFT: 'Borrador',
        OPEN: 'Abierto',
        CLOSED: 'Cerrado',
        CANCELLED: 'Cancelado',
    }
    creator = models.ForeignKey(MastersProfile, on_delete=models.CASCADE)
    post = models.ForeignKey(MarketPost, on_delete=models.PROTECT, related_name='offers')
    status = models.SmallIntegerField(choices=STATUSES.items(), default=DRAFT)
    already_closed = models.BooleanField(default=False)

    def __str__(self):
        return f'OFFER {self.id}|{self.creator} > {self.post}'


class MarketSlot(models.Model):
    MONEY = 0
    ITEM = 1
    POKEMON = 3
    ITEM_TYPES = {
        MONEY: 'Money',
        ITEM: 'Item',
        POKEMON: 'Pokemon'
    }

    item_type = models.SmallIntegerField(choices=ITEM_TYPES.items(), default=MONEY)
    banked_asset = models.ForeignKey(BankedAsset, on_delete=models.PROTECT, related_name='marketed', null=True,
                                     blank=True, limit_choices_to=Q(quantity__gt=0))
    quantity = models.PositiveIntegerField(default=1)
    post = models.ForeignKey(MarketPost, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    offer = models.ForeignKey(MarketPostOffer, on_delete=models.CASCADE, related_name='items', null=True, blank=True)

    def clean(self):
        if self.offer is not None and self.post is not None:
            raise ValidationError('offer and post should not be filled together')

        if self.offer is None and self.post is None:
            raise ValidationError('offer or post should be filled')


class MarketTransaction(models.Model):
    source = models.ForeignKey(MarketPost, on_delete=models.PROTECT)
    target = models.ForeignKey(MarketPostOffer, on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True)

    def perform_transaction(self, force_transaction=False):
        post = self.source
        offer = self.target

        if post.status != MarketPost.OPEN and not force_transaction:
            return

        if post.already_closed and not force_transaction:
            return

        with transaction.atomic():
            post.perform_transaction(offer.creator, force_transaction, self.id, offer.id)
            offer.perform_transaction(post.creator, force_transaction, self.id, offer.id)

        offer.already_closed = True
        offer.status = MarketPost.CLOSED
        offer.save()

        post.already_closed = True
        post.selected_offer = offer
        post.status = MarketPost.CLOSED
        post.save()

        for off in post.offers.exclude(id=offer.id):
            off.already_closed = True
            off.status = MarketPost.CANCELLED
            off.save()
