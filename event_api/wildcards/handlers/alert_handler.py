import json
from event_api.models import MastersProfile, Streamer
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer

from websocket.sockets import DataConsumer


@WildCardExecutorRegistry.register("alert_handler", verbose='Alert Handler')
class AlertHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    def execute(self, context):
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        target_id = context.get('target_id')[0]

        profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        streamer = profile.user.streamer_profile
        target_name = streamer.name
        data = dict(
            user_name=self.user.streamer_profile.name,
            wildcard=dict(
                name=self.wildcard.name,
                sprite_src=self.wildcard.sprite.url
            ),
            target_name=target_name
        )

        for chat in Streamer.objects.all().values_list('name', flat=True):
            # noinspection PyArgumentList
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat}',
                {
                    'type': 'chat.message',
                    'message': json.dumps(data)
                }
            )

        DataConsumer.send_custom_data(target_name, dict(
            type='attack_notification',
            data=data
        ))