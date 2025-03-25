from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, Streamer
from rewards_api.models import RewardBundle, Reward, ItemReward, MoneyReward, WildcardReward, PokemonReward
from trainer_data.models import Trainer


class ByteArrayFileField(serializers.FileField):
    def to_representation(self, value):
        """Lee los bytes del archivo y los convierte en una lista de enteros"""
        if not value:
            return None
        with value.open("rb") as f:
            return list(f.read())


class PokemonRewardSerializer(serializers.ModelSerializer):
    pokemon_data = ByteArrayFileField()

    class Meta:
        model = PokemonReward
        fields = (
            'pokemon_data',
            'pokemon_pid'
        )


class PokemonRewardSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PokemonReward
        fields = (
            'pokemon_pid',
        )


class WildcardRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = WildcardReward
        fields = (
            'wildcard',
            'quantity'
        )


class MoneyRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneyReward
        fields = ['quantity']


class ItemRewardSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    def get_item(self, obj):
        return obj.item.index

    class Meta:
        model = ItemReward
        fields = (
            'item',
            'quantity',
            'bag'
        )


class SimpleRewardSerializer(serializers.ModelSerializer):
    pokemon_reward = PokemonRewardSimpleSerializer()
    wildcard_reward = WildcardRewardSerializer()
    money_reward = MoneyRewardSerializer()
    item_reward = ItemRewardSerializer()

    class Meta:
        model = Reward
        fields = (
            'reward_type',
            'pokemon_reward',
            'wildcard_reward',
            'money_reward',
            'item_reward',
        )


class RewardSerializer(serializers.ModelSerializer):
    pokemon_reward = PokemonRewardSerializer()
    wildcard_reward = WildcardRewardSerializer()
    money_reward = MoneyRewardSerializer()
    item_reward = ItemRewardSerializer()

    class Meta:
        model = Reward
        fields = (
            'reward_type',
            'pokemon_reward',
            'wildcard_reward',
            'money_reward',
            'item_reward',
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
