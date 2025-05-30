from django.contrib.auth.models import User
from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, Streamer, GameEvent, GameMod
from trainer_data.models import Trainer


class SaveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaveFile
        fields = '__all__'


class WildcardSerializer(serializers.ModelSerializer):
    quality_display = serializers.CharField(source='get_quality_display')

    class Meta:
        model = Wildcard
        fields = '__all__'


class SimplifiedWildcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wildcard
        fields = ['id', 'name', 'sprite']


class WildcardWithInventorySerializer(serializers.ModelSerializer):
    quality_display = serializers.CharField(source='get_quality_display')
    inventory = serializers.SerializerMethodField()
    sprite_name = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.user: User = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def get_inventory(self, obj):
        streamer: Streamer = self.user.streamer_profile
        inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=obj).first()
        return inventory.quantity if inventory else 0

    class Meta:
        model = Wildcard
        fields = [
            'id',
            'name',
            'price',
            'special_price',
            'sprite',
            'description',
            'quality',
            'is_active',
            'extra_url',
            'always_available',
            'quality_display',
            'inventory',
            'sprite_name'
        ]


class GameModSerializer(serializers.ModelSerializer):

    class Meta:
        model = GameMod
        fields = [
            'mod_name',
            'mod_description'
        ]


class GameEventSerializer(serializers.ModelSerializer):
    game_mod = GameModSerializer()
    is_available = serializers.SerializerMethodField()

    def get_is_available(self, obj):
        return obj.is_available()

    class Meta:
        model = GameEvent
        fields = [
            'id',
            'game_mod',
            'is_available',
        ]
