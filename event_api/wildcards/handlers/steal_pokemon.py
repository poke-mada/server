from io import BytesIO

from django.core.files import File
from django.db import transaction

from event_api.models import CoinTransaction, MastersProfile, ErrorLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from rewards_api.models import Reward, RewardBundle, StreamerRewardInventory
from trainer_data.models import TrainerPokemon
from websocket.sockets import DataConsumer
from .strong_attack_handler import StrongAttackHandler


@WildCardExecutorRegistry.register("steal_pokemon", verbose='Steal Pokemon Handler')
class StealPokemonHandler(StrongAttackHandler):

    def validate(self, context):
        target_id = context.get('target_id')
        dex_number = context.get('dex_number')
        target_profile = MastersProfile.objects.get(id=target_id)

        if not dex_number:
            return 'Necesitas ingresar un pokemon a robar'

        if dex_number == target_profile.starter_dex_number:
            return 'No puedes robar al elegido de alguien mas'

        if dex_number == 658:
            return 'Greninja es inmune a los ataques!'

        # TODO falta validar que sea un pokemon robable:
        #  no debe haber pasado por tu partida, no debes tenerlo vivo, no debe estar baneado

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

        bundle = RewardBundle.objects.create(
            name='Steal Pokemon',
            user_created=True
        )

        new_premio = Reward.objects.create(
            reward_type=Reward.POKEMON,
            bundle=bundle
        )

        new_premio.pokemon_data.save(
            f"{target_pokemon.mote}.ek6",
            target_pokemon.enc_data.file,
            save=True
        )

        StreamerRewardInventory.objects.create(
            profile=self.user.masters_profile,
            reward=bundle
        )

        DataConsumer.send_custom_data(self.user.username, dict(
            type='notification',
            data='Te ha llegado un paquete al buzón!'
        ))

        return super().execute(context)
