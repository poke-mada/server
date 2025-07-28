from event_api.models import CoinTransaction, DeathLog, BannedPokemon
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from pokemon_api.models import Pokemon


@WildCardExecutorRegistry.register("release_pokemon", verbose='Venta Ilegal Handler')
class ReleasePokemonHandler(BaseWildCardHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        dex_number = context.get('dex_number')
        if not dex_number:
            return False

        last_death = DeathLog.objects.filter(dex_number=dex_number, profile=self.user.masters_profile, revived=False).first()
        if last_death:
            return False

        banned_mon = BannedPokemon.objects.filter(dex_number=dex_number, profile=self.user.masters_profile).first()
        if banned_mon:
            return False

        species_name = Pokemon.objects.filter(dex_number=dex_number).first().name
        BannedPokemon.objects.create(dex_number=dex_number, profile=self.user.masters_profile, species_name=species_name, reason='El pokemon se liberó con Venta Ilegal')

        money_quantity = self.wildcard.give_money_settings.quantity
        CoinTransaction.objects.create(
            profile=self.user.masters_profile,
            amount=money_quantity,
            TYPE=CoinTransaction.INPUT,
            reason=f'se uso la carta {self.wildcard.name} en {species_name}'
        )
        return True
