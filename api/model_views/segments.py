from django.utils import timezone
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response

from event_api.models import SegmentConfiguration, MastersProfile


class SegmentConfigurationSerializer(serializers.ModelSerializer):

    important_date = serializers.DateField()

    class Meta:
        model = SegmentConfiguration
        fields = ['starts_at', 'ends_at', 'is_tournament']


class SegmentConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SegmentConfiguration.objects.all()
    serializer_class = SegmentConfigurationSerializer

    @action(detail=False, methods=['get'])
    def next_date(self, request, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile
        current_segment = profile.current_segment_settings
        now = timezone.now()

        current_segment_config = SegmentConfiguration.objects.filter(
            is_tournament=False,
            ends_at__gt=now,
            segment=current_segment.segment
        ).first()

        if current_segment_config:
            if current_segment_config.starts_at < now:
                return Response(data=dict(segment=current_segment.segment, next_date=current_segment_config.ends_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), is_tournament=False, is_before=False), status=status.HTTP_200_OK)

            return Response(data=dict(segment=current_segment.segment, next_date=current_segment_config.starts_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), is_tournament=False, is_before=True), status=status.HTTP_200_OK)

        current_tournament_config = SegmentConfiguration.objects.filter(
            is_tournament=True,
            ends_at__gt=now,
            segment=current_segment.segment
        ).first()

        if not current_tournament_config:
            return Response(data=dict(segment=current_segment.segment, next_date=timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), is_tournament=False, is_before=False), status=status.HTTP_200_OK)

        if current_tournament_config.starts_at < now:
            return Response(data=dict(segment=current_segment.segment, next_date=current_tournament_config.ends_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), is_tournament=True, is_before=False), status=status.HTTP_200_OK)

        return Response(data=dict(segment=current_segment.segment, next_date=current_tournament_config.starts_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), is_tournament=True, is_before=True), status=status.HTTP_200_OK)

