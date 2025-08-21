from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from event_api.models import MastersProfile
from market.serializers import BankedAssetSimpleSerializer
from rewards_api.models import Roulette
from rewards_api.serializers import RouletteSimpleSerializer


class RouletteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Roulette.objects.all()
    serializer_class = RouletteSimpleSerializer

    @action(methods=['post'], detail=True)
    def roll(self, request, pk=None, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile

        queryset = profile.banked_assets.all()
        serialized = BankedAssetSimpleSerializer(queryset, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)
