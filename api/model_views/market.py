from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from market.models import MarketPost, MarketTransaction, MarketPostOffer
from market.serializers import MarketPostSerializer, MarketPostSimpleSerializer, MarketPostCreateSerializer, \
    MarketPostOfferCreateSerializer, MarketPostOfferSerializer


class MarketViewSet(viewsets.ModelViewSet):
    queryset = MarketPost.objects.all()
    serializer_class = MarketPostSerializer

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = MarketPost.objects.exclude(creator=request.user.masters_profile).order_by('-created_at')
        serializer = MarketPostSimpleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_mine(self, request, *args, **kwargs):
        queryset = MarketPost.objects.filter(status=MarketPost.OPEN, creator=request.user.masters_profile).order_by('-created_at')
        serializer = MarketPostSimpleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance: MarketPost):
        instance.status = MarketPost.CANCELLED
        instance.save()

    def create(self, request, *args, **kwargs):
        mesh_data = {
            **request.data,
            'creator': request.user.masters_profile.id
        }

        create_serializer = MarketPostCreateSerializer(data=mesh_data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()
        return_serializer = self.get_serializer(instance, read_only=True)
        headers = self.get_success_headers(return_serializer.data)
        return Response(return_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['put'], detail=True)
    def accept(self, request, pk=None, *args, **kwargs):
        offer_id = request.data.get('offer_id')
        instance = get_object_or_404(MarketPost, pk=pk, status=MarketPost.OPEN)
        get_object_or_404(MarketPostOffer, pk=offer_id, status=MarketPostOffer.OPEN)

        transaction: MarketTransaction = MarketTransaction.objects.create(
            source=instance,
            target_id=offer_id
        )

        transaction.perform_transaction()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def publish(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(MarketPost, pk=pk, status=MarketPost.DRAFT)

        instance.status = MarketPost.OPEN
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def offer(self, request, *args, **kwargs):
        get_object_or_404(MarketPost, id=request.data.get('post'), status=MarketPost.OPEN)

        mesh_data = {
            **request.data,
            'creator': request.user.masters_profile.id
        }
        create_serializer = MarketPostOfferCreateSerializer(data=mesh_data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()
        return_serializer = MarketPostOfferSerializer(instance, read_only=True)
        headers = self.get_success_headers(return_serializer.data)

        return Response(return_serializer.data, status=status.HTTP_200_OK, headers=headers)

    @action(methods=['put'], detail=True)
    def verify_offer(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(MarketPostOffer, pk=pk, status=MarketPostOffer.DRAFT)
        instance.status = MarketPostOffer.OPEN
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
