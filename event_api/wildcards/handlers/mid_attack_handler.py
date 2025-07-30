from decimal import Decimal

from event_api.models import MastersProfile, MastersSegmentSettings
from .attack_handler import AttackHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from websocket.sockets import DataConsumer


@WildCardExecutorRegistry.register("mid_attack", verbose='Mid Attack Handler')
class MidAttackHandler(AttackHandler):
    def validate(self, context):
        return True

    def execute(self, context):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings

        target_current_segment.karma += Decimal(0.5)
        target_current_segment.steal_karma += Decimal(0.5)
        target_current_segment.attacks_received_left -= Decimal(0.5)
        target_current_segment.save()

        DataConsumer.send_custom_data(target_profile.user.username, dict(
            type='karma',
            data=str(target_current_segment.karma)
        ))

        return super().execute(context)
