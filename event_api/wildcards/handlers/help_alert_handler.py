import json
from event_api.models import MastersProfile, Streamer, Newsletter
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer

from websocket.sockets import DataConsumer


@WildCardExecutorRegistry.register("help_alert_handler", verbose='Help Alert Handler')
class HelpAlertHandler(BaseWildCardHandler):
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
                sprite_src=''
            ),
            target_name=target_name
        )

        DataConsumer.send_custom_data(target_name, dict(
            type='help_notification',
            data=data
        ))

        Newsletter.objects.create(
            message=f'{self.user.streamer_profile.name} ha ayudado a {target_name} usando {self.wildcard.name}'
        )

        return True