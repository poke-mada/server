from event_api.wildcards.registry import WildCardExecutorRegistry
from pokemon_api.models import Pokemon
from .. import BaseWildCardHandler
from ...models import DeathLog


@WildCardExecutorRegistry.register("revive_pokemon", verbose='Revive Pokemon Handler')
class RevivePokemonHandler(BaseWildCardHandler):

    def execute(self, context):
        dex_number = context.get('dex_number')
        if not dex_number:
            return False

        last_death = DeathLog.objects.filter(dex_number=dex_number, profile=self.user.masters_profile, revived=False).first()
        if not last_death:
            return False

        last_death.revived = True
        last_death.save()

        return True
