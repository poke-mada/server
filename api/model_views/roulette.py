from django.db.models.functions import Random
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from event_api.models import MastersProfile
from rewards_api.models import Roulette, RewardBundle, Reward, RoulettePrice, StreamerRewardInventory, \
    RouletteRollHistory
from rewards_api.serializers import RouletteSimpleSerializer, RoulettePrizeSerializer, RouletteSerializer
from websocket.sockets import DataConsumer


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

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(user=self.request.user, *args, **kwargs)

    @action(methods=['post'], detail=True)
    def roll(self, request, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile
        roulette = self.get_object()
        if not profile.has_wildcard(roulette.wildcard):
            return Response('No Tienes comodines para esta tirada', status=status.HTTP_400_BAD_REQUEST)
        profile.consume_wildcard(roulette.wildcard)

        price: RoulettePrice = roulette.spin()

        bundle = RewardBundle.objects.create(
            name=f'Comodin Ganado por {roulette.name}',
            user_created=True,
            sender='Ruleta'
        )

        RouletteRollHistory.objects.create(
            profile=profile,
            roulette=roulette,
            message=f'{profile.streamer_name} tiró {roulette.name} y ganó {price.name}'
        )

        for prize in price.wildcards.all():
            Reward.objects.create(
                reward_type=Reward.WILDCARD,
                bundle=bundle,
                wildcard=prize.wildcard,
                quantity=prize.quantity
            )

        StreamerRewardInventory.objects.create(
            profile=profile,
            reward=bundle
        )

        DataConsumer.send_custom_data(request.user.username, dict(
            type='notification',
            data='Te ha llegado un paquete al buzón!'
        ))

        serializer = RoulettePrizeSerializer(price)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        roulette = self.get_object()
        serializer = RouletteSerializer(roulette)
        return Response(serializer.data, status=status.HTTP_200_OK)


