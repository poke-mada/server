import boto3
from botocore.config import Config
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import Round
from rest_framework import serializers

from rewards_api.models import RewardBundle, Reward, Roulette, RoulettePrice


class ByteArrayFileField(serializers.FileField):
    def to_representation(self, value):
        """Lee los bytes del archivo y los convierte en una lista de enteros"""
        if not value:
            return None
        with value.open("rb") as f:
            return list(f.read())


class PokemonPIDField(serializers.FileField):
    def to_representation(self, value):
        """Lee los bytes del archivo y los convierte en una lista de enteros"""
        if not value:
            return None

        return hex(value)


class SimpleRewardSerializer(serializers.ModelSerializer):
    pokemon_pid = PokemonPIDField()
    bag = serializers.SerializerMethodField()

    def get_bag(self, obj: Reward):
        if not obj.item:
            return None
        return obj.item.item_bag

    class Meta:
        model = Reward
        fields = (
            'reward_type',
            'pokemon_pid',
            'bag',
            'item',
            'wildcard',
            'quantity',
        )


class RewardSerializer(serializers.ModelSerializer):
    pokemon_data = ByteArrayFileField()
    bag = serializers.SerializerMethodField()

    def get_bag(self, obj: Reward):
        if not obj.item:
            return None
        return obj.item.item_bag

    class Meta:
        model = Reward
        fields = (
            'reward_type',
            'pokemon_data',
            'bag',
            'item',
            'wildcard',
            'quantity',
        )


class StreamerRewardSimpleSerializer(serializers.ModelSerializer):
    rewards = SimpleRewardSerializer(many=True, read_only=True)

    class Meta:
        model = RewardBundle
        fields = [
            'id',
            'name',
            'description',
            'rewards'
        ]


class StreamerRewardSerializer(serializers.ModelSerializer):
    rewards = RewardSerializer(many=True, read_only=True)

    class Meta:
        model = RewardBundle
        fields = [
            'id',
            'name',
            'description',
            'rewards'
        ]


class RoulettePrizeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='wildcard.sprite', read_only=True, use_url=True)

    class Meta:
        model = RoulettePrice
        fields = [
            'id',
            'name',
            'image'
        ]


class RouletteSimpleSerializer(serializers.ModelSerializer):
    prize_probability = serializers.SerializerMethodField()
    total_prizes = serializers.SerializerMethodField()

    def get_total_prizes(self, obj):
        total_prices = obj.prices.count()
        return total_prices

    def get_prize_probability(self, obj):
        total_prices = obj.prices.count()
        if total_prices == 0:
            return None

        probs = obj.prices.values('name').annotate(probability=Round(Count('name') * (100 / total_prices), 2)).order_by(
            '-probability', 'name')

        return probs

    class Meta:
        model = Roulette
        fields = [
            'id',
            'name',
            'description',
            'prize_probability',
            'total_prizes',
            'banner_logo',
            'banner_image'
        ]


class RouletteSerializer(serializers.ModelSerializer):
    prices = RoulettePrizeSerializer(many=True, read_only=True)

    class Meta:
        model = Roulette
        fields = [
            'id',
            'name',
            'description',
            'prices',
            'banner_logo',
            'banner_image'
        ]
