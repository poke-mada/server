from io import BytesIO

from django.core.files import File
from rest_framework import serializers

from event_api.models import Newsletter
from pokemon_api.models import Type, Pokemon, Item, Move, PokemonNature, PokemonAbility, ContextLocalization
from pokemon_api.serializers import PokemonSerializer, TypeSerializer, MoveSerializer, PokemonNatureSerializer
from trainer_data.models import Trainer, TrainerBox, TrainerPokemon, TrainerTeam, TrainerBoxSlot


class BytesField(serializers.Field):
    def to_representation(self, value):
        return list(value)  # lista de enteros en vez de string

    def to_internal_value(self, data):
        return bytes(data)  # reconstruir desde lista


class TrainerPokemonSerializer(serializers.ModelSerializer):
    pokemon = PokemonSerializer(required=False)
    dex_number = serializers.IntegerField(required=False)
    held_item = serializers.IntegerField(required=False)
    ability = serializers.IntegerField(required=False)
    nature = serializers.IntegerField(required=False)
    types = serializers.ListField(child=serializers.DictField())
    moves = serializers.ListField()
    enc_data = BytesField(required=False)

    def create(self, validated_data):
        dex_number = validated_data.pop('dex_number')
        held_item = validated_data.pop('held_item')
        nature = validated_data.pop('nature')
        ability = validated_data.pop('ability')
        enc_data = validated_data.pop('enc_data')

        form = validated_data.pop('form', '0')
        types = validated_data.pop('types')
        moves = validated_data.pop('moves')

        possible_mons = Pokemon.objects.filter(dex_number=dex_number)
        pokemon_obj = possible_mons.filter(form=form).first()
        if not pokemon_obj:
            pokemon_obj = possible_mons.first()

        held_item_obj = Item.objects.get(index=held_item, localization='en')
        nature_obj = PokemonNature.objects.get(index=nature, localization='en')
        ability_obj = PokemonAbility.objects.get(index=ability, localization='en')

        in_types = []
        for type_ in types:
            type_object = Type.objects.get(name__iexact=type_['name'])
            in_types.append(type_object)

        in_moves = []
        for move_ in moves:
            move_object = Move.objects.get(index=move_)
            in_moves.append(move_object)

        validated_data['pokemon'] = pokemon_obj
        validated_data['nature'] = nature_obj
        validated_data['held_item'] = held_item_obj
        validated_data['ability'] = ability_obj
        pokemon = TrainerPokemon.objects.create(**validated_data)

        buffer = BytesIO()
        buffer.write(enc_data)
        buffer.seek(0)  # muy importante para que lea desde el inicio

        pokemon.enc_data.save(
            f"pokemon/{pokemon.mote}.ek6",
            File(buffer),
            save=True
        )

        pokemon.moves.set(in_moves)
        pokemon.types.set(in_types)
        return pokemon

    class Meta:
        model = TrainerPokemon
        fields = '__all__'


class TrainerTeamSerializer(serializers.ModelSerializer):
    team = TrainerPokemonSerializer(many=True)

    def create(self, validated_data):
        team = validated_data.pop('team')
        trainer_team = super().create(validated_data)
        for pokemon in team:
            serializer = TrainerPokemonSerializer(data=pokemon)
            if serializer.is_valid(raise_exception=True):
                pokemon = serializer.save()
                trainer_team.team.add(pokemon)

        return trainer_team

    class Meta:
        model = TrainerTeam
        fields = '__all__'


# noinspection PyMethodMayBeStatic
class ROTrainerPokemonSerializer(serializers.ModelSerializer):
    localization = 'es'
    nature = PokemonNatureSerializer()
    species = serializers.CharField(source='pokemon.name', read_only=True)
    dex_number = serializers.IntegerField(source='pokemon.dex_number', read_only=True)

    mega_ability = serializers.IntegerField(source='mega_ability.index', read_only=True)
    ability = serializers.IntegerField(source='ability.index', read_only=True)
    held_item = serializers.IntegerField(source='held_item.index', read_only=True)

    held_item_name = serializers.SerializerMethodField()
    held_item_flavor = serializers.SerializerMethodField()
    ability_name = serializers.SerializerMethodField()
    ability_flavor = serializers.SerializerMethodField()
    nature_name = serializers.SerializerMethodField()
    mega_ability_name = serializers.SerializerMethodField()
    mega_ability_flavor = serializers.SerializerMethodField()

    sprite_url = serializers.SerializerMethodField()
    moves = MoveSerializer(many=True)
    types = TypeSerializer(many=True)

    def get_held_item_name(self, obj: TrainerPokemon):
        name_localization: ContextLocalization = obj.held_item.name_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.held_item.name_localizations.first()
        return name_localization.content

    def get_held_item_flavor(self, obj: TrainerPokemon):
        flavor_localization: ContextLocalization = obj.held_item.flavor_text_localizations.filter(
            language='*'
        ).first()
        if not flavor_localization:
            flavor_localization = obj.held_item.flavor_text_localizations.first()
        return flavor_localization.content if flavor_localization else ''

    def get_ability_name(self, obj: TrainerPokemon):
        name_localization: ContextLocalization = obj.ability.name_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.ability.name_localizations.first()
        return name_localization.content

    def get_mega_ability_name(self, obj: TrainerPokemon):
        if not obj.mega_ability:
            return None
        name_localization: ContextLocalization = obj.mega_ability.name_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.mega_ability.name_localizations.first()
        return name_localization.content

    def get_mega_ability_flavor(self, obj: TrainerPokemon):
        if not obj.mega_ability:
            return None
        name_localization: ContextLocalization = obj.mega_ability.flavor_text_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.mega_ability.flavor_text_localizations.first()
        return name_localization.content

    def get_ability_flavor(self, obj: TrainerPokemon):
        flavor_localization: ContextLocalization = obj.ability.flavor_text_localizations.filter(
            language='*'
        ).first()
        if not flavor_localization:
            flavor_localization = obj.ability.flavor_text_localizations.first()

        return flavor_localization.content if flavor_localization else ''

    def get_nature_name(self, obj: TrainerPokemon):
        name_localization: ContextLocalization = obj.nature.name_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.nature.name_localizations.first()
        return name_localization.content

    def get_sprite_url(self, obj: TrainerPokemon):
        return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{obj.pokemon.dex_number}.png'

    class Meta:
        model = TrainerPokemon
        fields = [
            'dex_number', 'species', 'sprite_url', 'mote', 'held_item', 'held_item_name', 'ability', 'ability_name',
            'nature', 'nature_name', 'pokemon', 'types', 'moves', 'level', 'cur_hp', 'max_hp', 'attack', 'defense',
            'speed', 'special_attack', 'special_defense', 'held_item_flavor', 'ability_flavor', 'ev_hp',
            'ev_attack', 'ev_defense', 'ev_speed', 'ev_special_attack', 'ev_special_defense', 'iv_hp', 'iv_attack',
            'iv_defense', 'iv_speed', 'iv_special_attack', 'iv_special_defense', 'mega_ability', 'mega_ability_name',
            'mega_ability_flavor', 'suffix'
        ]


class EnROTrainerPokemonSerializer(ROTrainerPokemonSerializer):
    moves = MoveSerializer(many=True, localization='en')
    localization = 'en'


class ROTrainerTeamSerializer(serializers.ModelSerializer):
    team = ROTrainerPokemonSerializer(read_only=True, many=True)

    class Meta:
        model = TrainerTeam
        fields = ['team']


class EnROTrainerTeamSerializer(ROTrainerTeamSerializer):
    team = EnROTrainerPokemonSerializer(read_only=True, many=True)


class TrainerSerializer(serializers.ModelSerializer):
    current_team = ROTrainerTeamSerializer(read_only=True)

    class Meta:
        model = Trainer
        fields = ['id', 'name', 'current_team']


class EnTrainerSerializer(TrainerSerializer):
    current_team = EnROTrainerTeamSerializer(read_only=True)


class SelectTrainerSerializer(serializers.ModelSerializer):
    streamer_name = serializers.SerializerMethodField()

    def get_streamer_name(self, obj):
        return obj.streamer_name()

    class Meta:
        model = Trainer
        fields = ['id', 'name', 'streamer_name']


class TrainerBoxSlotSerializer(serializers.ModelSerializer):
    pokemon = ROTrainerPokemonSerializer(read_only=True)

    class Meta:
        model = TrainerBoxSlot
        fields = ['slot', 'pokemon']


class TrainerBoxSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    owner_profile = serializers.SerializerMethodField()
    stealable = serializers.SerializerMethodField()
    box_identifier = serializers.SerializerMethodField()
    slots = TrainerBoxSlotSerializer(many=True, read_only=True)

    def get_owner(self, obj):
        return obj.trainer.id

    def get_stealable(self, obj):
        return obj.trainer.get_trainer_profile().current_segment_settings.experience > 0

    def get_owner_profile(self, obj):
        return obj.trainer.get_trainer_profile().id

    def get_box_identifier(self, obj):
        if obj.name:
            return obj.name
        return f"Box #{obj.box_number + 1}"

    class Meta:
        model = TrainerBox
        fields = ['owner', 'owner_profile', 'box_number', 'box_identifier', 'name', 'slots', 'stealable']


class ListedBoxSerializer(serializers.ModelSerializer):
    box_identifier = serializers.SerializerMethodField()

    def get_box_identifier(self, obj):
        if obj.name:
            return obj.name
        return f"Box #{obj.box_number + 1}"

    class Meta:
        model = TrainerBox
        fields = ['box_number', 'box_identifier', 'name']


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = '__all__'
