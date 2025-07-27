from event_api.models import MastersProfile, MastersSegmentSettings
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from websocket.sockets import DataConsumer
from .alert_handler import AlertHandler


@WildCardExecutorRegistry.register("strong_attack", verbose='Strong Attack Handler')
class StrongAttackHandler(AlertHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings
        source_current_segment: MastersSegmentSettings = self.user.masters_profile.current_segment_settings
        if target_current_segment.attacks_received_left < self.wildcard.karma_consumption:
            return 'cannot_attack'

        target_current_segment.karma += self.wildcard.karma_consumption
        target_current_segment.steal_karma += self.wildcard.karma_consumption
        target_current_segment.attacks_received_left -= self.wildcard.karma_consumption
        target_current_segment.save()

        source_current_segment.karma -= self.wildcard.karma_consumption
        source_current_segment.save()

        DataConsumer.send_custom_data(self.user.masters_profile.streamer_name, dict(
            type='karma',
            data=str(source_current_segment.karma)
        ))

        DataConsumer.send_custom_data(target_profile.streamer_name, dict(
            type='karma',
            data=str(target_current_segment.karma)
        ))

        return super().execute(context)
