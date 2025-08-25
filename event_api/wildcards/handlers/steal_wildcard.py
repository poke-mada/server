from django.db.models.functions import Random

from event_api.models import CoinTransaction, MastersProfile, StreamerWildcardInventoryItem
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from .attack_handler import AttackHandler


@WildCardExecutorRegistry.register("steal_wildcard", verbose='Steal Wildcard Handler')
class StealWildcardHandler(AttackHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context, avoid_notification=False):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        source_profilie: MastersProfile = self.user.masters_profile
        wildcard_to_steal: StreamerWildcardInventoryItem = target_profile.wildcard_inventory.filter(quantity__gte=1).order_by(Random()).first()

        target_profile.consume_wildcard(wildcard_to_steal.wildcard, 1)
        source_profilie.give_wildcard(wildcard_to_steal.wildcard, 1)

        return super().execute(context, avoid_notification=avoid_notification)
