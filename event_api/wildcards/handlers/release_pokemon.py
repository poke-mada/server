from event_api.models import CoinTransaction, DeathLog, BannedPokemon
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from pokemon_api.models import Pokemon


@WildCardExecutorRegistry.register("release_pokemon", verbose='Venta Ilegal Handler')
class ReleasePokemonHandler(BaseWildCardHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def validate(self, context):
        profile = self.user.masters_profile
        dex_number = context.get('dex_number')
        if not dex_number:
            return 'Necesitas seleccionar un pokemon a liberar'

        last_non_revived_death = DeathLog.objects.filter(dex_number=dex_number, profile=profile,
                                                         revived=False)
        if last_non_revived_death:
            return 'Este pokemon está muerto'

        banned = BannedPokemon.objects.filter(dex_number=dex_number, profile=profile)

        if banned:
            return 'Este pokemon está baneado'

        last_pokemon_version = profile.get_last_releasable_by_dex_number(dex_number)

        if last_pokemon_version.is_shiny:
            return 'El pokemon no puede ser shiny'
        return super().validate(context)

    def execute(self, context):
        dex_number = context.get('dex_number')

        released_pokemon = Pokemon.objects.filter(dex_number=dex_number).first()
        banned_forms = released_pokemon.surrogate()
        for pokemon in banned_forms:
            BannedPokemon.objects.create(
                dex_number=pokemon.dex_number,
                profile=self.user.masters_profile,
                species_name=pokemon.name,
                reason='El pokemon se liberó con Venta Ilegal'
            )

        money_quantity = self.wildcard.give_money_settings.quantity
        CoinTransaction.objects.create(
            profile=self.user.masters_profile,
            amount=money_quantity,
            TYPE=CoinTransaction.INPUT,
            segment=self.user.masters_profile.current_segment_settings.segment,
            reason=f'se uso la carta {self.wildcard.name} en {released_pokemon.name}'
        )
        return True
