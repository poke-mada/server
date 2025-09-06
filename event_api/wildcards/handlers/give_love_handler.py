from django.db.models import Q

from pokemon_api.models import Item
from rewards_api.models import Reward, StreamerRewardInventory, RewardBundle
from .help_alert_handler import HelpAlertHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.models import MastersProfile, Wildcard, WildcardLog


@WildCardExecutorRegistry.register("give_love", verbose='Give Love Handler')
class GiveLoveHandler(HelpAlertHandler):

    def validate(self, context):
        source_profile = self.user.masters_profile
        target_id = context.get('target_id', False)

        if not target_id:
            return 'Necesitas seleccionar un objetivo'

        target_profile: MastersProfile = MastersProfile.objects.filter(id=target_id).first()

        if not target_profile:
            return 'Selecciona un objetivo valido'

        if source_profile.current_segment_settings.segment != target_profile.current_segment_settings.segment:
            return 'No puedes ayudar a alguien de otro tramo'

        return True

    def execute(self, context):
        source_profile = self.user.masters_profile
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        bundle = RewardBundle.objects.create(
            name=f'Ayuda enviada por {source_profile.streamer_name}',
            user_created=True,
            sender=source_profile.streamer_name,
            type=RewardBundle.WILDCARD_BUNDLE
        )

        Reward.objects.create(
            reward_type=Reward.ITEM,
            item=Item.objects.filter(index=24).first(),
            quantity=2,
            bundle=bundle
        )

        StreamerRewardInventory.objects.create(
            profile=target_profile,
            reward=bundle
        )

        WildcardLog.objects.create(
            profile=source_profile,
            wildcard=self.wildcard,
            details=f'Comodin usado en {target_profile.streamer_name}'
        )
