
from websocket.sockets import DataConsumer
from .alert_handler import AlertHandler
from ...models import MastersSegmentSettings


class AttackHandler(AlertHandler):

    def validate(self, context):
        from event_api.models import MastersProfile, Wildcard
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings
        if target_current_segment.attacks_received_left < self.wildcard.karma_consumption or target_current_segment.attacks_received_right <= 0:
            return 'Ya no puedes atacar a este objetivo'
        return True
