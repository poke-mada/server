import json
from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response

from new_market.models import BankPokemon, MarketBlockLog, MarketCooldownLog, BankItem, MarketRoom
from pokemon_api.models import Item
from trainer_data.models import TrainerPokemon


class BankPokemonSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankPokemon
        fields = '__all__'


class MarketViewSet(viewsets.ModelViewSet):
    queryset = MarketRoom.objects.all()
    serializer_class = BankPokemonSerializer

    @action(detail=False, methods=['post'])
    def transfer_pokemon(self, request, *args, **kwargs):
        profile = request.user.masters_profile
        pokemon_id = request.data.get('pokemon_id', 0)
        pokemon = TrainerPokemon.objects.get(id=pokemon_id)

        now = timezone.now()
        is_blocked_to_market = MarketCooldownLog.objects.filter(
            profile=profile,
            dex_number=pokemon.pokemon.dex_number,
            blocked_until__gt=now
        ).exists()

        if is_blocked_to_market:
            return Response(data='El pokemon esta en tiempo de espera por 24 horas', status=status.HTTP_400_BAD_REQUEST)

        BankPokemon.objects.create(
            trainer_pokemon=pokemon,
            owner=profile
        )

        MarketBlockLog.objects.create(
            dex_number=pokemon.pokemon.dex_number,
            profile=profile,
            blocked_until=(timezone.now() + timedelta(minutes=15))
        )

        MarketCooldownLog.objects.create(
            dex_number=pokemon.pokemon.dex_number,
            profile=profile,
            blocked_until=(timezone.now() + timedelta(hours=24))
        )

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def transfer_items(self, request, *args, **kwargs):
        item_data = request.data.get('items', False)

        if not item_data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        json_data = json.loads(item_data)
        for item in json_data:
            item_obj = Item.objects.filter(index=item['index']).first()
            BankItem.objects.create(
                owner=request.user.masters_profile,
                item=item_obj,
                quantity=item['quantity']
            )

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def create_room(self, request, *args, **kwargs):
        profile = request.user.masters_profile
        room = MarketRoom.objects.create(
            owner=profile,
            name=f'Sala de {profile.streamer_name}'
        )

        return Response(room.id, status=status.HTTP_201_CREATED)