from rest_framework import serializers

from pokemon_api.models import Type, Pokemon, Item, Move, PokemonNature, PokemonAbility, ContextLocalization
from pokemon_api.serializers import PokemonSerializer, TypeSerializer, MoveSerializer
from trainer_data.models import Trainer, TrainerBox, TrainerPokemon, TrainerTeam, TrainerBoxSlot


class TrainerPokemonSerializer(serializers.ModelSerializer):
    pokemon = PokemonSerializer(required=False)
    dex_number = serializers.IntegerField(required=False)
    held_item = serializers.IntegerField(required=False)
    ability = serializers.IntegerField(required=False)
    nature = serializers.IntegerField(required=False)
    types = serializers.ListField(child=serializers.DictField())
    moves = serializers.ListField()

    def create(self, validated_data):
        dex_number = validated_data.pop('dex_number')
        held_item = validated_data.pop('held_item')
        nature = validated_data.pop('nature')
        ability = validated_data.pop('ability')

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
    localization = '*'
    held_item_name = serializers.SerializerMethodField()
    held_item_flavor = serializers.SerializerMethodField()
    ability_name = serializers.SerializerMethodField()
    ability_flavor = serializers.SerializerMethodField()
    nature_name = serializers.SerializerMethodField()
    sprite_url = serializers.SerializerMethodField()
    held_item = serializers.SerializerMethodField()
    ability = serializers.SerializerMethodField()
    nature = serializers.SerializerMethodField()
    pokemon = PokemonSerializer()
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

    def get_ability_flavor(self, obj: TrainerPokemon):
        flavor_localization: ContextLocalization = obj.ability.flavor_text_localizations.filter(
            language='*'
        ).first()
        print(flavor_localization)
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

    def get_held_item(self, obj: TrainerPokemon):
        return obj.held_item.index

    def get_ability(self, obj: TrainerPokemon):
        return obj.ability.index

    def get_nature(self, obj: TrainerPokemon):
        return obj.nature.index

    def get_sprite_url(self, obj: TrainerPokemon):
        return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{obj.pokemon.dex_number}.png'

    class Meta:
        model = TrainerPokemon
        fields = [
            'sprite_url', 'mote', 'held_item', 'held_item_name', 'ability', 'ability_name', 'nature',
            'nature_name', 'pokemon', 'types', 'moves', 'level', 'cur_hp', 'max_hp', 'attack', 'defense',
            'speed', 'special_attack', 'special_defense', 'notes', 'held_item_flavor', 'ability_flavor'
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
        fields = ['name', 'custom_sprite', 'current_team', 'economy']


class EnTrainerSerializer(TrainerSerializer):
    current_team = EnROTrainerTeamSerializer(read_only=True)


class SelectTrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ['name', 'streamer_name']


class TrainerBoxSlotSerializer(serializers.ModelSerializer):
    pokemon = ROTrainerPokemonSerializer(read_only=True)

    class Meta:
        model = TrainerBoxSlot
        fields = ['slot', 'pokemon']


class TrainerBoxSerializer(serializers.ModelSerializer):
    box_identifier = serializers.SerializerMethodField()
    slots = TrainerBoxSlotSerializer(many=True, read_only=True)

    def get_box_identifier(self, obj):
        if obj.name:
            return obj.name
        return f"Box #{obj.box_number + 1}"

    class Meta:
        model = TrainerBox
        fields = ['box_number', 'box_identifier', 'name', 'slots']
