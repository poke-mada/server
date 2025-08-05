from rest_framework import viewsets, status
from rest_framework.response import Response

from event_api.models import MastersProfile
from market.models import MarketPost, BankedAsset
from market.serializers import BankedAssetSimpleSerializer


class BankViewSet(viewsets.ModelViewSet):
    queryset = BankedAsset.objects.all()
    serializer_class = BankedAssetSimpleSerializer

    def list(self, request, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile
        queryset = profile.banked_assets.all()
        serialized = BankedAssetSimpleSerializer(queryset, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)
