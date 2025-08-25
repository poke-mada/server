from datetime import datetime, timedelta

from rest_framework import viewsets, status
from rest_framework.response import Response

from event_api.models import MastersProfile, ProfileNotification
from event_api.serializers import ProfileNotificationSimpleSerializer


class ProfileNotificationViewSet(viewsets.ModelViewSet):
    queryset = ProfileNotification.objects.all()
    serializer_class = ProfileNotificationSimpleSerializer

    def list(self, request, *args, **kwargs):
        profile: MastersProfile = request.user.masters_profile
        queryset = self.get_queryset().filter(profile=profile, created_at=(datetime.now() - timedelta(hours=24))).order_by('-created_at')
        serialized = self.serializer_class(queryset, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)
