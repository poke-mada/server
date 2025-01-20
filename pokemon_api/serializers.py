from rest_framework import serializers

from pokemon_api.models import Pokemon, Item, Type, MoveCategory, Move, PokemonNature, PokemonAbility, \
    ContextLocalization


class PokemonAbilitySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PokemonAbility


class PokemonNatureSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PokemonNature


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Item


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['name']
        model = Type


class MoveCategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = MoveCategory


class PokemonSerializer(serializers.ModelSerializer):
    types = TypeSerializer(read_only=True, many=True)

    class Meta:
        fields = '__all__'
        model = Pokemon


# noinspection PyMethodMayBeStatic
class MoveSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.localization = kwargs.pop('localization', '*')
        super(MoveSerializer, self).__init__(*args, **kwargs)

    move_type = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    double_damage_to = serializers.SerializerMethodField()
    half_damage_to = serializers.SerializerMethodField()
    no_damage_to = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_double_damage_to(self, obj: Move):
        return obj.double_damage_to

    def get_half_damage_to(self, obj: Move):
        return obj.half_damage_to

    def get_no_damage_to(self, obj: Move):
        return obj.no_damage_to

    def get_category(self, obj: Move):
        return obj.category.name

    def get_move_type(self, obj: Move):
        return obj.move_type.name

    def get_name(self, obj: Move):
        name_localization: ContextLocalization = obj.name_localizations.filter(
            language=self.localization
        ).first()
        if not name_localization:
            name_localization = obj.name_localizations.first()
        return name_localization.content

    class Meta:
        fields = '__all__'
        model = Move

