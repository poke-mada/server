from rest_framework import serializers

from event_api.models import MastersProfile
from trainer_data.models import Trainer, TrainerPokemon


class PokemonOverlaySerializer(serializers.ModelSerializer):
    sprite_url = serializers.SerializerMethodField()

    def get_sprite_url(self, obj: TrainerPokemon):
        return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{obj.pokemon.dex_number}.png'

    class Meta:
        fields = ['sprite_url', 'mote']
        model = TrainerPokemon


class OverlaySerializer(serializers.ModelSerializer):
    team = PokemonOverlaySerializer(read_only=True, many=True, source='current_team.team', default=[])
    gym1 = serializers.BooleanField(read_only=True, source='gym_badge_1')
    gym2 = serializers.BooleanField(read_only=True, source='gym_badge_2')
    gym3 = serializers.BooleanField(read_only=True, source='gym_badge_3')
    gym4 = serializers.BooleanField(read_only=True, source='gym_badge_4')
    gym5 = serializers.BooleanField(read_only=True, source='gym_badge_5')
    gym6 = serializers.BooleanField(read_only=True, source='gym_badge_6')
    gym7 = serializers.BooleanField(read_only=True, source='gym_badge_7')
    gym8 = serializers.BooleanField(read_only=True, source='gym_badge_8')
    death_count = serializers.SerializerMethodField()

    def get_death_count(self, obj: Trainer):
        profile: MastersProfile = obj.get_trainer_profile()
        return profile.death_count

    class Meta:
        fields = [
            'team',
            'gym1',
            'gym2',
            'gym3',
            'gym4',
            'gym5',
            'gym6',
            'gym7',
            'gym8',
            'death_count'
        ]
        model = Trainer
