from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from api.permissions import IsRoot
from pokemon_api.models import Type, Pokemon, Move, MoveCategory, PokemonNature, Item, PokemonAbility, TypeCoverage, \
    ContextLocalization


def load_pokemon_data():
    with open('data/mon_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for dex_number, mon in json_data.items():
            for form, data in mon.items():
                types_names = [t['name'] for t in data['types']]
                types = Type.objects.filter(name__in=types_names)
                pokemon, _ = Pokemon.objects.get_or_create(
                    dex_number=dex_number,
                    name=data['name'],
                    form=form
                )
                pokemon.types.add(*types)
    return 'pokemon'


def load_types_data():
    with open('data/types.json', 'r') as data_file:
        json_data = json.load(data_file)
        for index, type in json_data.items():
            Type.objects.get_or_create(index=index, name=type, localization='en')
    return 'types'


def load_types_coverages_data():
    with open('data/type_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for type, coverage in json_data.items():
            type_from = Type.objects.get(name__iexact=type)
            double_damage_to = coverage['double_damage_to']
            half_damage_to = coverage['half_damage_to']
            no_damage_to = coverage['no_damage_to']

            for damage_to in double_damage_to:
                type_to = Type.objects.get(name__iexact=damage_to)
                TypeCoverage.objects.get_or_create(type_from=type_from, type_to=type_to, multiplier=2)

            for damage_to in half_damage_to:
                type_to = Type.objects.get(name__iexact=damage_to)
                TypeCoverage.objects.get_or_create(type_from=type_from, type_to=type_to, multiplier=0.5)

            for damage_to in no_damage_to:
                type_to = Type.objects.get(name__iexact=damage_to)
                TypeCoverage.objects.get_or_create(type_from=type_from, type_to=type_to, multiplier=0)

    return 'coverages'


def load_moves_data():
    with open('data/move_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for index, move in json_data.items():
            type_obj = Type.objects.get(name=move['typename'])
            category_obj = MoveCategory.objects.get(name=move['movecategoryname'])
            Move.objects.get_or_create(
                index=index,
                localization="es",
                name=move['movename'],
                max_pp=move['movepp'],
                move_type=type_obj,
                power=int(move['movepower']),
                accuracy=int(move['moveaccuracy']),
                contact_flag=int(move['movecontactflag']) == 1,
                category=category_obj,
                flavor_text=move['falvor_text']
            )
    with open('data/en/move_data.json') as fp:
        json_data = json.load(fp)
        for index, move in json_data.items():
            move_obj = Move.objects.get(index=index)
            loc, _ = ContextLocalization.objects.get_or_create(language='en', content=move['movename'])
            move_obj.name_localizations.add(loc)
    return 'moves'


def load_natures_data():
    with open('data/nature_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for index, nature in json_data.items():
            PokemonNature.objects.get_or_create(index=index, name=nature['name'], localization='en')
    return 'natures'


def load_items_data():
    with open('data/item_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for index, item in json_data.items():
            Item.objects.get_or_create(index=index, name=item['name'], localization='en')
    return 'items'


def load_abilities_data():
    with open('data/ability_data.json', 'r') as data_file:
        json_data = json.load(data_file)
        for index, ability in json_data.items():
            PokemonAbility.objects.get_or_create(index=index, name=ability['name'], localization='en')
    with open('data/ability_data.json') as fp:
        json_data = json.load(fp)
        for index, ability in json_data.items():
            ability_obj = PokemonAbility.objects.get(index=index)
            loc, _ = ContextLocalization.objects.get_or_create(language='en',
                                                               content=ability['flavor_text'])
            ability_obj.flavor_text_localizations.add(loc)
    return 'abilities'


class LoadJsonDataView(APIView):
    permission_classes = [IsAuthenticated, IsRoot]

    def get(self, request, *args, **kwargs):
        loaded_types = load_types_data()
        loaded_natures = load_natures_data()
        loaded_abilities = load_abilities_data()
        loaded_items = load_items_data()
        loaded_moves = load_moves_data()
        loaded_pokemon = load_pokemon_data()
        loaded_types_coverages = load_types_coverages_data()
        return Response(data={
            loaded_pokemon,
            loaded_types,
            loaded_moves,
            loaded_natures,
            loaded_items,
            loaded_abilities,
            loaded_types_coverages
        }, status=status.HTTP_200_OK)
