import json
from event_api.models import Streamer
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer


@WildCardExecutorRegistry.register("alert_handler", verbose='Alert Handler')
class AlertHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    def execute(self, context):
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        target_id = context.get('target_id')[0]

        streamer = Streamer.objects.get(id=target_id)

        data = dict(
            user_name=self.user.streamer_profile.name,
            wildcard=dict(
                name=self.wildcard.name,
                sprite_src=self.wildcard.sprite.url
            ),
            target_name=streamer.name
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
