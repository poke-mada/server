import os
import boto3
from botocore.config import Config
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from event_api.models import MastersProfile
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
    name = serializers.SerializerMethodField()
    mote_or_quantity = serializers.SerializerMethodField()
    sprite = serializers.SerializerMethodField()

    def get_mote_or_quantity(self, obj: MarketSlot):
        if obj.item_type == MarketSlot.MONEY:
            return obj.quantity

        if obj.item_type == MarketSlot.ITEM:
            return obj.quantity

        if obj.item_type == MarketSlot.POKEMON:
            return obj.banked_asset.object.mote

    def get_name(self, obj: MarketSlot):
        if obj.item_type == MarketSlot.MONEY:
            return "Deditas"

        if obj.item_type == MarketSlot.ITEM:
            return obj.banked_asset.object.name

        if obj.item_type == MarketSlot.POKEMON:
            return obj.banked_asset.object.pokemon.name

        return obj

    def get_sprite(self, obj: MarketSlot):
        if obj.item_type == MarketSlot.MONEY:
            return "./assets/coin.png"

        if obj.item_type == MarketSlot.ITEM:
            item: Item = obj.banked_asset.object
            if item.custom_sprite:
                presigned_url = cache.get(f'cached_item_url_{item.id}')
                STORAGE_TIMEOUT = 60 * 15
                if not presigned_url:
                    documento = item.custom_sprite

                    file_field = documento.file
                    s3_key = file_field.name  # Ej: "documentos/archivo.pdf"
                    ENVIRONMENT = os.getenv("DJANGO_ENV", "prod")  # "dev", "stage" o "prod"
                    full_s3_path = os.path.join(ENVIRONMENT, 'dedsafio-pokemon/media', s3_key)
                    s3_path_cache = full_s3_path
                    s3 = boto3.client(
                        's3',
                        region_name='us-east-1',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        config=Config(signature_version='s3v4', s3={"use_accelerate_endpoint": True})
                    )
                    presigned_url = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_path_cache},
                        ExpiresIn=STORAGE_TIMEOUT,
                    )
                item_sprite_url = presigned_url
            else:
                item_name = item.name
                snake_item_name = item_name.lower().replace(" ", "-")
                item_sprite_url = f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{snake_item_name}.png'
            return item_sprite_url

        if obj.item_type == MarketSlot.POKEMON:
            return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{obj.banked_asset.object.pokemon.index}.png'

        return obj

    class Meta:
        model = MarketSlot
        fields = [
            'sprite',
            'name',
            'mote_or_quantity'
        ]


class MarketSlotCreatePostSerializer(serializers.ModelSerializer):
    item_type = serializers.IntegerField(required=False, allow_null=True)
    banked_asset = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = MarketSlot
        fields = [
            'item_type',
            'quantity',
            'banked_asset'
        ]


class MarketPostSimpleSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.streamer_name', read_only=True)
    items = MarketSlotListSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPost
        fields = [
            'id',
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items'
        ]


class MarketOfferSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    creator_photo = serializers.ImageField(source='creator.web_picture', read_only=True, use_url=True)
    creator = serializers.CharField(source='creator.streamer_name', read_only=True)

    class Meta:
        model = MarketPostOffer
        fields = [
            'id',
            'creator',
            'creator_photo',
            'status',
            'status_display',
            'already_closed',
            'items'
        ]


class MarketPostSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    offers = MarketOfferSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPost
        fields = [
            'id',
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items',
            'offers'
        ]


class MarketPostCreateSerializer(serializers.ModelSerializer):
    items = MarketSlotCreatePostSerializer(many=True)

    class Meta:
        model = MarketPost
        fields = [
            'creator',
            'items',
        ]

    def validate(self, data):
        owner: MastersProfile = data['creator']
        for item in data['items']:
            quantity = item['quantity']
            asset_id = item.get('banked_asset', False)
            asset: BankedAsset = BankedAsset.objects.filter(id=asset_id).first()
            item_type = 0 if not asset else 1 if asset.content_type.model == 'item' else 3
            match item_type:
                case MarketSlot.ITEM:
                    if not owner.has_item(asset, quantity):
                        raise ValidationError(
                            'No dispones de suficientes unidades de este objeto, o se encuentra bloqueado por otra oferta')
                case MarketSlot.POKEMON:
                    if not owner.has_item(asset, quantity):
                        raise ValidationError('Los Pokemon solo se pueden cambiar 1 a la vez')
                case MarketSlot.MONEY:
                    if not owner.economy >= quantity:
                        raise ValidationError('No tienes tanto dinero')

        return super().validate(data)

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items')

        post = MarketPost.objects.create(**validated_data)
        for item in items:
            asset_id = item.pop('banked_asset', None)
            if asset_id and item.get('item_type', 7) != MarketSlot.MONEY:
                asset: BankedAsset = BankedAsset.objects.filter(id=asset_id).first()

                MarketSlot.objects.create(
                    banked_asset=asset,
                    quantity=item['quantity'],
                    item_type=1 if asset.content_type.model == 'item' else 2,
                    post=post
                )
            elif item.get('item_type', 7) == MarketSlot.MONEY:
                MarketSlot.objects.create(
                    **item,
                    post=post
                )

        return post


class MarketPostOfferCreateSerializer(serializers.ModelSerializer):
    items = MarketSlotCreatePostSerializer(many=True)

    class Meta:
        model = MarketPostOffer
        fields = [
            'post',
            'creator',
            'items',
        ]

    def validate(self, data):
        owner: MastersProfile = data['creator']
        for item in data['items']:
            quantity = item['quantity']
            asset_id = item.get('banked_asset', False)
            asset: BankedAsset = BankedAsset.objects.filter(id=asset_id).first()
            item_type = 0 if not asset else 1 if asset.content_type.model == 'item' else 3
            print(item_type)
            match item_type:
                case MarketSlot.ITEM:
                    if not owner.has_item(asset, quantity):
                        raise ValidationError(
                            'No dispones de suficientes unidades de este objeto, o se encuentra bloqueado por otra oferta')
                case MarketSlot.POKEMON:
                    if not owner.has_item(asset, quantity):
                        raise ValidationError('Los Pokemon solo se pueden cambiar 1 a la vez')
                case MarketSlot.MONEY:
                    if not owner.economy >= quantity:
                        raise ValidationError('No tienes tanto dinero')

        return super().validate(data)

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items')

        offer = MarketPostOffer.objects.create(**validated_data)
        for item in items:
            asset_id = item.pop('banked_asset', None)
            if asset_id and item.get('item_type', 7) != MarketSlot.MONEY:
                asset: BankedAsset = BankedAsset.objects.filter(id=asset_id).first()

                MarketSlot.objects.create(
                    banked_asset=asset,
                    quantity=item['quantity'],
                    item_type=1 if asset.content_type.model == 'item' else 2,
                    offer=offer
                )
            elif item.get('item_type', 7) == MarketSlot.MONEY:
                MarketSlot.objects.create(
                    **item,
                    offer=offer
                )

        return offer


class MarketPostOfferSerializer(serializers.ModelSerializer):
    items = MarketSlotListSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketPostOffer
        fields = [
            'id',
            'post',
            'creator',
            'status',
            'status_display',
            'already_closed',
            'items'
        ]
