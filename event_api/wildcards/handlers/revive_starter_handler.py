from event_api.wildcards.registry import WildCardExecutorRegistry
from pokemon_api.models import Pokemon
from .. import BaseWildCardHandler
from ...models import DeathLog, BannedPokemon


@WildCardExecutorRegistry.register("revive_starter", verbose='Revive Starter Handler')
class ReviveStarterHandler(BaseWildCardHandler):

    def validate(self, context):

        if not self.user.masters_profile.starter_dex_number:
            return 'Necesitas decirle al staff cual es tu inicial'

    def execute(self, context):
        last_death = DeathLog.objects.filter(dex_number=self.user.masters_profile.starter_dex_number, profile=self.user.masters_profile, revived=False).first()
        last_death.revived = True
        last_death.save()
        return True
