from rest_framework import viewsets, status
from rest_framework.response import Response

from market.models import MarketPost
from market.serializers import MarketPostSerializer, MarketPostSimpleSerializer


class MarketViewSet(viewsets.ModelViewSet):
    queryset = MarketPost.objects.all()
    serializer_class = MarketPostSerializer

    def list(self, request, *args, **kwargs):
        queryset = MarketPost.objects.filter(status=MarketPost.OPEN).order_by('-created_at')
        serializer = MarketPostSimpleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

