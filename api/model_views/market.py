from rest_framework import viewsets

from new_market.models import BankPokemon


class MarketViewSet(viewsets.ModelViewSet):
    queryset = BankPokemon.objects.all()

    def transfer_pokemon(self, request, *args, **kwargs):
        pass