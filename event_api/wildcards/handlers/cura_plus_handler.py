from django.db.models import Q

from .help_alert_handler import HelpAlertHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.models import MastersProfile, Wildcard, WildcardLog


@WildCardExecutorRegistry.register("heal_plus", verbose='Cura Plus Handler')
class HealPlusHandler(HelpAlertHandler):

    def validate(self, context):
        target_id = context.get('target_id', False)

        if not target_id:
            return 'Necesitas seleccionar un objetivo'

        target_profile: MastersProfile = MastersProfile.objects.filter(id=target_id).first()

        if not target_profile:
            return 'Selecciona un objetivo valido'

        return True

    def execute(self, context):
        source_profile = self.user.masters_profile
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        if target_profile:
            notification = f'Regalo de {source_profile.streamer_name}'
            target_profile.give_wildcard(Wildcard.objects.get(Q(id=5) | Q(name__iexact='revivir pokemon')), notification=notification)
            WildcardLog.objects.create(
                profile=source_profile,
                wildcard=self.wildcard,
                details=f'Comodin usado en {target_profile.streamer_name}'
            )
