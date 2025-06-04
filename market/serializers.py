from rest_framework import serializers
from .models import TransactionLog, TradeOffer, TradeProposal, BankedAsset, Pokemon, Item, Moneda


class RelatedObjectField(serializers.Field):
    def to_representation(self, value):
        if isinstance(value, Pokemon):
            return {
                "type": "Pokemon",
                "id": value.id,
                "name": value.nombre
            }
        elif isinstance(value, Item):
            return {
                "type": "Item",
                "id": value.id,
                "name": value.nombre
            }
        elif isinstance(value, Moneda):
            return {
                "type": "Moneda",
                "id": value.id,
                "amount": value.cantidad
            }
        elif isinstance(value, TradeOffer):
            return {
                "type": "TradeOffer",
                "id": value.id
            }
        elif isinstance(value, TradeProposal):
            return {
                "type": "TradeProposal",
                "id": value.id
            }
        else:
            return {
                "type": str(type(value)),
                "id": getattr(value, "id", None)
            }


class TransactionLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Asume que el __str__ del usuario es el nombre
    related_object = RelatedObjectField()

    class Meta:
        model = TransactionLog
        fields = [
            "id",
            "user",
            "action",
            "related_object",
            "description",
            "created_at",
            "meta"
        ]
