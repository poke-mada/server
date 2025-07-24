from event_api.models import MastersProfile, MastersSegmentSettings
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from .alert_handler import AlertHandler


@WildCardExecutorRegistry.register("strong_attack", verbose='Strong Attack Handler')
class MidAttackHandler(AlertHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        target_id = context.get('target_id')[0]
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings
        source_current_segment: MastersSegmentSettings = self.user.masters_profile.current_segment_settings

        target_current_segment.karma += self.wildcard.karma_consumption
        target_current_segment.attacks_received_left -= self.wildcard.karma_consumption
        target_current_segment.save()

        source_current_segment.karma -= self.wildcard.karma_consumption
        source_current_segment.save()

        return super().execute(context)
