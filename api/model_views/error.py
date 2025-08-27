from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response

from event_api.models import ErrorLog


class ErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorLog
        fields = ['id']


class ErrorLogViewSet(viewsets.ModelViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer

    @action(methods=['post'], detail=False)
    def register(self, request, *args, **kwargs):
        details = request.data.get('details')
        error = ErrorLog.objects.create(
            profile=self.request.user.masters_profile,
            details=details,
            message=f'Mensaje reportado desde la app'
        )

        return Response(data=error.id, status=status.HTTP_200_OK)