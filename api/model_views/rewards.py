from rest_framework import viewsets

from rewards_api.models import RewardBundle
from rewards_api.serializers import RewardBundleSerializer


class RewardsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RewardBundle.objects.all()
    serializer_class = RewardBundleSerializer
