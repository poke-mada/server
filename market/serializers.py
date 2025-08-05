from rest_framework import serializers

from pokemon_api.models import Item
from trainer_data.models import TrainerPokemon
from .models import BankedAsset, MarketPost, MarketSlot, MarketPostOffer


class RelatedObjectField(serializers.Field):
    def to_representation(self, object):
        if isinstance(object, TrainerPokemon):
            return {
                "type": "Pokemon",
                "id": object.id,
                "dex_number": object.pokemon.dex_number,
                "name": object.mote,
                "species": object.pokemon.name
            }
        elif isinstance(object, Item):
            return {
                "type": "Item",
                "id": object.id,
                "index": object.index,
                "name": object.name
            }
        else:
            return {
                "type": str(type(object)),
                "id": getattr(object, "id", None)
            }


# class TransactionLogSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField()  # Asume que el __str__ del usuario es el nombre
#     related_object = RelatedObjectField()
#
#     class Meta:
#         model = TransactionLog
#         fields = [
#             "id",
#             "user",
#             "action",
#             "related_object",
#             "description",
#             "created_at",
#             "meta"
#         ]


class BankedAssetSimpleSerializer(serializers.ModelSerializer):
    object = RelatedObjectField()

    class Meta:
        model = BankedAsset
        fields = [
            'id',
            'object_id',
            'object',
            'quantity',
            'trade_locked',
            'origin'
        ]


class MarketSlotListSerializer(serializers.ModelSerializer):
    banked_asset = BankedAssetSimpleSerializer()

    class Meta:
        model = MarketSlot
        fields = [
            'quantity',
            'banked_asset'
        ]


class MarketPostSimpleSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPost
        fields = [
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items'
        ]


class MarketOfferSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPostOffer
        fields = [
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items'
        ]


class MarketPostSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    offers = MarketOfferSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPost
        fields = [
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items',
            'offers'
        ]
