from django.db.models import Q

from .help_alert_handler import HelpAlertHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.models import MastersProfile, Wildcard, WildcardLog


@WildCardExecutorRegistry.register("mega_revive", verbose='Mega Revive Handler')
class MegaReviveHandler(HelpAlertHandler):

    def execute(self, context):
        source_profile = self.user.masters_profile

        notification = f'Mega Revivir usado'
        source_profile.give_wildcard(Wildcard.objects.get(Q(id=5) | Q(name__iexact='revivir pokemon')), 5, notification=notification)
