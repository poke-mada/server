from cProfile import Profile

from django.contrib.auth.models import User
from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, Streamer, GameEvent, GameMod, \
    MastersProfile
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
    quality_display = serializers.CharField(source='get_category_display')
    inventory = serializers.SerializerMethodField()
    sprite_name = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.user: User = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def get_inventory(self, obj):
        profile: MastersProfile = self.user.masters_profile
        inventory: StreamerWildcardInventoryItem = profile.wildcard_inventory.filter(wildcard=obj).first()
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
            'category',
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


class SelectProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj: MastersProfile):
        try:
            return obj.user.streamer_profile.name
        except TypeError:
            return None

    class Meta:
        model = MastersProfile
        fields = [
            'id',
            'name'
        ]


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj: MastersProfile):
        try:
            return obj.user.streamer_profile.name
        except TypeError:
            return None

    class Meta:
        model = MastersProfile
        fields = [
            'id',
            'name',
            'save_path',
            'tournament_league',
            'is_pro',
            'web_picture',
            'death_count'
        ]
