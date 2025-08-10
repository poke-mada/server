from io import BytesIO

from django.core.files import File
from django.db import transaction

from event_api.models import CoinTransaction, MastersProfile, ErrorLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from rewards_api.models import Reward, RewardBundle, StreamerRewardInventory
from trainer_data.models import TrainerPokemon
from .strong_attack_handler import StrongAttackHandler


@WildCardExecutorRegistry.register("steal_pokemon", verbose='Steal Pokemon Handler')
class StealPokemonHandler(StrongAttackHandler):

    def validate(self, context):
        dex_number = context.get('dex_number')

        if not dex_number:
            return 'Necesitas ingresar un pokemon a robar'

        return super().validate(context)

    @transaction.atomic
    def execute(self, context):
        target_id = context.get('target_id')
        dex_number = context.get('dex_number')

        target_profile = MastersProfile.objects.get(id=target_id)
        target_pokemon: TrainerPokemon = target_profile.get_last_releasable_by_dex_number(dex_number)

        if not target_pokemon:
            error = ErrorLog.objects.create(
                profile=self.user.masters_profile,
                message=f"No se encontro el pokemon para el dex_num {dex_number} en el perfil de {target_id}: {target_profile.streamer_name}"
            )
            return f'error: {error.id}'

        reward = RewardBundle.objects.create(
            name='Steal Pokemon'
        )

        new_premio = Reward.objects.create(
            reward_type=Reward.POKEMON,
            reward=reward
        )

        buffer = BytesIO()
        buffer.write(target_pokemon.enc_data)
        buffer.seek(0)  # muy importante para que lea desde el inicio

        new_premio.pokemon_data.save(
            f"{target_pokemon.mote}.ek6",
            File(buffer),
            save=True
        )

        StreamerRewardInventory.objects.create(
            profile=self.user.masters_profile,
            reward=reward
        )

        return super().execute(context)
