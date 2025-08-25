import json
from event_api.models import MastersProfile, Newsletter, ProfileNotification
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer
from websocket.sockets import DataConsumer
from asgiref.sync import async_to_sync


@WildCardExecutorRegistry.register("alert_handler", verbose='Alert Handler')
class AlertHandler(BaseWildCardHandler):
    def execute(self, context, avoid_notification=False):
        channel_layer = get_channel_layer()
        target_id = context.get('target_id')

        profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_name = profile.streamer_name
        data = dict(
            user_name=self.user.masters_profile.streamer_name,
            wildcard=dict(
                name=self.wildcard.name,
                sprite_src=''
            ),
            target_name=target_name
        )

        for chat in MastersProfile.objects.filter(
                is_pro=profile.is_pro,
                is_tester=profile.is_tester,
                profile_type=MastersProfile.TRAINER
        ).values_list('streamer_name', flat=True):
            # noinspection PyArgumentList
            try:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{chat}',
                    dict(type='chat.message', message=json.dumps(data))
                )
            except:
                continue

        DataConsumer.send_custom_data(profile.user.username, dict(
            type='attack_notification',
            data=data
        ))

        profile = self.user.masters_profile
        Newsletter.objects.create(
            message=f'<strong>{self.user.masters_profile.streamer_name}</strong> ha atacado a <strong>{target_name}</strong> usando <strong>{self.wildcard.name}</strong>',
            for_noobs=(not profile.is_pro),
            for_pros=profile.is_pro,
            for_staff=self.user.is_staff,
            for_tester=profile.is_tester
        )
        ProfileNotification.objects.create(
            profile=profile,
            message=f'<strong>{self.user.masters_profile.streamer_name}</strong> te ha atacado usando <strong>{self.wildcard.name} a {avoid_notification}</strong>'
        )

        return True
