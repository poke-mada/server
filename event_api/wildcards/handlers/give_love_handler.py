from django.db.models import Q

from pokemon_api.models import Item
from rewards_api.models import Reward, StreamerRewardInventory, RewardBundle
from .help_alert_handler import HelpAlertHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.models import MastersProfile, Wildcard, WildcardLog


@WildCardExecutorRegistry.register("give_love", verbose='Give Love Handler')
class GiveLoveHandler(HelpAlertHandler):

    def execute(self, context):
        source_profile = self.user.masters_profile
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        bundle = RewardBundle.objects.create(
            name=f'Ayuda enviada por {source_profile.streamer_name}',
            user_created=True
        )

        Reward.objects.create(
            reward_type=Reward.ITEM,
            item=Item.objects.filter(index=24).first(),
            bundle=bundle
        )

        StreamerRewardInventory.objects.create(
            profile=target_profile,
            reward=bundle
        )

        notification = f'Regalo de {source_profile.streamer_name}'

        target_profile.give_wildcard(Wildcard.objects.get(Q(id=5) | Q(name__iexact='revivir pokemon')),
                                     notification=notification)
        WildcardLog.objects.create(
            profile=source_profile,
            wildcard=self.wildcard,
            details=f'Comodin usado en {target_profile.streamer_name}'
        )
