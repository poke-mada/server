from event_api.wildcards.registry import WildCardExecutorRegistry
from pokemon_api.models import Pokemon
from .. import BaseWildCardHandler
from ...models import DeathLog, BannedPokemon


@WildCardExecutorRegistry.register("revive_pokemon", verbose='Revive Pokemon Handler')
class RevivePokemonHandler(BaseWildCardHandler):
    def execute(self, context):
        last_death = DeathLog.objects.filter(dex_number=self.user.masters_profile.starter_dex_number, profile=self.user.masters_profile, revived=False).first()
        last_death.revived = True
        last_death.save()
        return True
