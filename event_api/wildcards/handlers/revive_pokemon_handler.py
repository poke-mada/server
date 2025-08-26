from event_api.wildcards.registry import WildCardExecutorRegistry
from pokemon_api.models import Pokemon
from .. import BaseWildCardHandler
from ...models import DeathLog, BannedPokemon


@WildCardExecutorRegistry.register("revive_pokemon", verbose='Revive Pokemon Handler')
class RevivePokemonHandler(BaseWildCardHandler):

    def validate(self, context):
        dex_number = context.get('dex_number')
        if not dex_number:
            return 'Necesitas seleccionar un pokemon a revivir'

        last_non_revived_death = DeathLog.objects.filter(dex_number=dex_number, profile=self.user.masters_profile, revived=False)
        if not last_non_revived_death:
            return 'Este pokemon no está muerto'

        if DeathLog.objects.filter(dex_number=dex_number, profile=self.user.masters_profile).exists():
            return 'No puedes revivir dos veces un pokemon'

        banned = BannedPokemon.objects.filter(dex_number=dex_number, profile=self.user.masters_profile)
        if banned:
            return 'Este pokemon está baneado'

        return super().validate(context)

    def execute(self, context):
        dex_number = context.get('dex_number')
        last_death = DeathLog.objects.filter(dex_number=dex_number, profile=self.user.masters_profile, revived=False).first()

        last_death.revived = True
        last_death.save()
        return True
