from .alert_handler import AlertHandler
from ...models import MastersSegmentSettings


class AttackHandler(AlertHandler):

    def validate(self, context):
        from event_api.models import MastersProfile
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings
        if target_current_segment.attacks_received_left < self.wildcard.karma_consumption or target_current_segment.attacks_received_left <= 0:
            return 'Ya no puedes atacar a este objetivo'

        if target_profile.current_segment_settings.segment > self.user.masters_profile.current_segment_settings.segment:
            return 'No puedes atacar a nadie que este en un tramo mas adelante'

        if target_profile.in_pokemon_league:
            return 'No puedes atacar a alguien que haya empezado la liga pokemon'

        return True
