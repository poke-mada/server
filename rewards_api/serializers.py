from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, Streamer
from rewards_api.models import RewardBundle, Reward
from trainer_data.models import Trainer


class RewardSerializer(serializers.ModelSerializer):
    reward = serializers.SerializerMethodField()

    def get_reward(self, obj):
        return obj.get_reward()

    class Meta:
        model = Reward
        fields = (
            'reward_type',
            'is_active',
            'reward'
        )


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
