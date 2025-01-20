from rest_framework import serializers

from event_api.models import SaveFile


class SaveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaveFile
        fields = '__all__'
