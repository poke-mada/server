from event_api.models import DeathLog, Evolution
from event_api.wildcards.registry import WildCardExecutorRegistry
from pokemon_api.models import Pokemon
from .. import BaseWildCardHandler


@WildCardExecutorRegistry.register("revive_starter", verbose='Revive Starter Handler')
class ReviveStarterHandler(BaseWildCardHandler):

    def validate(self, context):

        if not self.user.masters_profile.starter_dex_number:
            return 'Necesitas decirle al staff cual es tu inicial'

        starter: Pokemon = Evolution.objects.filter(dex_number=self.user.masters_profile.starter_dex_number).first()
        starter_tree = starter.surrogate()

        if not DeathLog.objects.filter(dex_number__in=starter_tree, profile=self.user.masters_profile, revived=False).exists():
            return 'El pokemon no está registrado como muerto'

    def execute(self, context):
        starter: Pokemon = Evolution.objects.filter(dex_number=self.user.masters_profile.starter_dex_number).first()
        starter_tree = starter.surrogate()
        last_death = DeathLog.objects.filter(dex_number__in=starter_tree, profile=self.user.masters_profile, revived=False).first()
        last_death.revived = True
        last_death.save()
        return True
