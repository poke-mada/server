import json
from event_api.models import MastersProfile, Streamer, Newsletter
from event_api.wildcards.handlers.settings.models import TimerHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from channels.layers import get_channel_layer

from websocket.sockets import DataConsumer


@WildCardExecutorRegistry.register("timer_handler", verbose='Timer Handler')
class TimerHandler(BaseWildCardHandler):
    admin_inline_model = TimerHandlerSettings  # a model with extra config

    def validate(self, context):
        return

    def execute(self, context):
        DataConsumer.send_custom_data(self.user.streamer_profile.name, dict(
            type='start_timer_notification',
            data=self.wildcard.timer_handler_settings
        ))

        return True
