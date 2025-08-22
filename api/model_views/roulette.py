from django.db.models.functions import Random
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from event_api.models import MastersProfile
from rewards_api.models import Roulette
from rewards_api.serializers import RouletteSimpleSerializer, RoulettePrizeSerializer


class RouletteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Roulette.objects.all().order_by('order')
    serializer_class = RouletteSimpleSerializer

    def get_queryset(self):
        request = self.request
        profile: MastersProfile = request.user.masters_profile
        current_segment = profile.current_segment_settings
        if not current_segment:
            queryset = super().get_queryset().filter(segment=1)
        else:
            queryset = super().get_queryset().filter(segment=current_segment.segment)
        return queryset

    @action(methods=['post'], detail=True)
    def roll(self, request, pk=None, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile
        roulette = self.get_object()
        if not profile.has_wildcard(roulette.wildcard):
            return Response('No Tienes comodines para esta tirada', status=status.HTTP_400_BAD_REQUEST)

        profile.consume_wildcard(roulette.wildcard)

        price = roulette.prices.all().order_by(Random()).first()
        serializer = RoulettePrizeSerializer(price)
        return Response(serializer.data, status=status.HTTP_200_OK)
