import json
from event_api.models import Streamer
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer


@WildCardExecutorRegistry.register("alert_handler", verbose='Alert Handler')
class AlertHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    async def execute(self, context):
        from websocket.sockets import MyConsumer
        channel_layer = get_channel_layer()
        target_id = context.get('target_id')

        streamer = Streamer.objects.get(id=target_id)

        data = dict(
            user_name=self.user.streamer_profile.name,
            wildcard=dict(
                name=self.wildcard.name,
                sprite_src=self.wildcard.sprite
            ),
            target_name=streamer.name
        )

        for chat in MyConsumer.chats:
            print(chat)
            await channel_layer.group_send(chat, dict(type='chat', text=json.dumps(data)))
