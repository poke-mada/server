from django.db.models import Count
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
    image = serializers.CharField(source='wildcard.sprite', read_only=True)

    class Meta:
        model = RoulettePrice
        fields = [
            'id',
            'name',
            'image'
        ]


class RouletteSimpleSerializer(serializers.ModelSerializer):
    price_probability = serializers.SerializerMethodField()

    def get_price_probability(self, obj):
        total_prices = obj.prices.count()
        if total_prices == 0:
            return None

        probs = obj.prices.values('name').annotate(probability=Count('name') * (100 / total_prices))

        return probs

    class Meta:
        model = Roulette
        fields = [
            'id',
            'name',
            'description',
            'prize_probability'
        ]
