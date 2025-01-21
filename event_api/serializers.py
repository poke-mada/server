from rest_framework import serializers

from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, Streamer
from trainer_data.models import Trainer


class SaveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaveFile
        fields = '__all__'


class WildcardSerializer(serializers.ModelSerializer):
    quality_display = serializers.CharField(source='get_quality_display')

    class Meta:
        model = Wildcard
        fields = '__all__'


class WildcardWithInventorySerializer(serializers.ModelSerializer):
    quality_display = serializers.CharField(source='get_quality_display')
    inventory = serializers.SerializerMethodField()
    sprite_name = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.trainer: Trainer = kwargs.pop('trainer')
        super().__init__(*args, **kwargs)

    def get_inventory(self, obj):
        streamer: Streamer = self.trainer.streamer.first()
        inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=obj).first()
        return inventory.quantity if inventory else 0

    class Meta:
        model = Wildcard
        fields = [
            'name',
            'price',
            'special_price',
            'sprite',
            'description',
            'quality',
            'is_active',
            'extra_url',
            'always_available',
            'quality_display',
            'inventory',
            'sprite_name'
        ]
