from event_api.models import CoinTransaction, MastersProfile
from event_api.wildcards.registry import WildCardExecutorRegistry
from .strong_attack_handler import StrongAttackHandler


@WildCardExecutorRegistry.register("steal_pokemon", verbose='Steal Pokemon Handler')
class StealPokemonHandler(StrongAttackHandler):

    def validate(self, context):
        
        return super().validate(context)

    def execute(self, context):
        target_id = context.get('target_id')
        dex_number = context.get('dex_number')

        return super().execute(context)
