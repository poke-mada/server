from django.db.models.functions import Random

from event_api.models import MastersProfile, StreamerWildcardInventoryItem, ProfileNotification, \
    Wildcard
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from .attack_handler import AttackHandler


@WildCardExecutorRegistry.register("steal_wildcard", verbose='Steal Wildcard Handler')
class StealWildcardHandler(AttackHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context, *args, **kwargs):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        source_profilie: MastersProfile = self.user.masters_profile
        wildcard_to_steal: StreamerWildcardInventoryItem = target_profile.wildcard_inventory.exclude(wildcard__category=Wildcard.PROTECT).filter(quantity__gte=1).order_by(Random()).first()
        if not wildcard_to_steal:
            ProfileNotification.objects.create(
                profile=target_profile,
                message=f'No has podido robar ningún comodín a <strong>{target_profile.streamer_name}</strong>'
            )

        target_profile.consume_wildcard(wildcard_to_steal.wildcard, 1)
        source_profilie.give_wildcard(wildcard_to_steal.wildcard, 1)

        ProfileNotification.objects.create(
            profile=target_profile,
            message=f'<strong>{self.user.masters_profile.streamer_name}</strong> te ha robado el comodin <strong>{wildcard_to_steal.wildcard.name}</strong>'
        )

        return super().execute(context, avoid_notification=True)
