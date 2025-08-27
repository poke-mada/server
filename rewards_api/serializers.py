from django.db.models import Sum
from django.db.models.functions import Round
from rest_framework import serializers

from event_api.models import Wildcard
from pokemon_api.models import Item
from rewards_api.models import RewardBundle, Reward, Roulette, RoulettePrice, RouletteRollHistory


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
            'rewards',
            'sender',
            'type'
        ]


class WildcardDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Wildcard
        fields = ('name', 'sprite')


class ItemDisplaySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name_localizations.get(language='es').content

    class Meta:
        model = Item
        fields = ('name', 'index')


class DisplayRewardSerializer(serializers.ModelSerializer):
    wildcard = WildcardDisplaySerializer()
    item = ItemDisplaySerializer()
    pokemon = serializers.SerializerMethodField()

    def get_pokemon(self, obj):
        if not obj.pokemon_data:
            return None
        from pokemon_api.scripting.save_reader import PokemonBytes
        pokemon = PokemonBytes(obj.pokemon_data.read())
        pokemon.get_atts()
        dict_data = pokemon.to_dict()
        del dict_data['enc_data']
        return dict_data

    class Meta:
        model = Reward
        fields = [
            'reward_type',
            'quantity',
            'wildcard',
            'item',
            'pokemon'
        ]


class StreamerRewardSerializer(serializers.ModelSerializer):
    rewards = DisplayRewardSerializer(many=True, read_only=True)

    class Meta:
        model = RewardBundle
        fields = [
            'id',
            'name',
            'description',
            'rewards'
        ]


class RoulettePrizeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True, use_url=True)
    jackpot = serializers.BooleanField(source='is_jackpot', read_only=True)

    class Meta:
        model = RoulettePrice
        fields = [
            'id',
            'name',
            'image',
            'jackpot'
        ]


class RouletteHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RouletteRollHistory
        fields = [
            'message'
        ]


class RouletteSimpleSerializer(serializers.ModelSerializer):
    prize_probability = serializers.SerializerMethodField()
    total_prizes = serializers.SerializerMethodField()
    wishes = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    def get_total_prizes(self, obj):
        total_prices = obj.prices.aggregate(total_prizes=Sum('weight'))['total_prizes']
        return total_prices or 0

    def get_wishes(self, obj: Roulette):
        profile = self.user.masters_profile
        qs = profile.wildcard_inventory.filter(wildcard=obj.wildcard).aggregate(total_wildcards=Sum('quantity'))

        return qs['total_wildcards'] or 0

    def get_prize_probability(self, obj: Roulette):
        total_prices = obj.prices.aggregate(total_prizes=Sum('weight'))['total_prizes'] or 0
        if total_prices == 0:
            return []

        probs = obj.prices.values('image', 'name').annotate(
            probability=Round((Sum('weight') * 100.0) / total_prices, 2)
        ).order_by(
            '-probability', 'name'
        )

        return probs

    def get_history(self, obj):
        profile = self.user.masters_profile
        return RouletteHistorySerializer(profile.roulette_hiistory.filter(roulette=obj), many=True).data

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Roulette
        fields = [
            'id',
            'name',
            'description',
            'prize_probability',
            'total_prizes',
            'banner_logo',
            'active_banner_logo',
            'banner_image',
            'wishes',
            'history'
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
