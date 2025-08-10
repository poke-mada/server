from django.db import transaction

from event_api.models import MastersProfile
from event_api.wildcards.registry import WildCardExecutorRegistry
from .steal_pokemon import StealPokemonHandler


@WildCardExecutorRegistry.register("karma_steal_pokemon", verbose='Steal Karma Pokemon Handler')
class KarmaStealPokemonHandler(StealPokemonHandler):

    def validate(self, context):
        context['bypasses_reverse'] = True
        profile = self.user.masters_profile
        current_segment = profile.current_segment_settings

        if current_segment.steal_karma < 3:
            return 'Necesitas suficiente karma justo para esto'

        return super().validate(context)

    @transaction.atomic
    def execute(self, context):
        source_current_segment = self.user.masters_profile.current_segment_settings

        source_current_segment.steal_karma -= 3
        source_current_segment.save()

        return super().execute(context)
