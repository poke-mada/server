from cProfile import Profile

from django.contrib.auth.models import User
from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, GameEvent, GameMod, \
    MastersProfile, DeathLog
from trainer_data.models import Trainer, TrainerPokemon


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

    class Meta:
        model = GameEvent
        fields = [
            'id',
            'name',
            'available_date_from',
            'available_date_to',
            'description',
            'requirements',
            'free_join',
            'can_join',
            'is_available',
            'game_mod',
        ]


class SelectProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj: MastersProfile):
        try:
            return obj.streamer_name
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
            return obj.streamer_name
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


class SelectMastersProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MastersProfile
        fields = [
            'id',
            'streamer_name'
        ]


class DeathLogSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def get_value(self, obj: DeathLog):
        return obj.dex_number

    def get_title(self, obj: DeathLog):
        return f'{obj.dex_number} - {obj.mote or obj.species_name}'

    class Meta:
        model = DeathLog
        fields = [
            'value',
            'title'
        ]


class ReleasableSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def get_value(self, obj: TrainerPokemon):
        return obj.pokemon.dex_number

    def get_title(self, obj: TrainerPokemon):
        return f'{obj.pokemon.dex_number} - {obj.mote or obj.pokemon.name}'

    class Meta:
        model = TrainerPokemon
        fields = [
            'value',
            'title'
        ]
