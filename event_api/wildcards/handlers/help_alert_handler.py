from event_api.models import MastersProfile, Newsletter
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler

from websocket.sockets import DataConsumer


@WildCardExecutorRegistry.register("help_alert_handler", verbose='Help Alert Handler')
class HelpAlertHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    def execute(self, context):
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

        DataConsumer.send_custom_data(target_name, dict(
            type='help_notification',
            data=data
        ))

        Newsletter.objects.create(
            message=f'{self.user.masters_profile.streamer_name} ha ayudado a {target_name} usando {self.wildcard.name}'
        )

        return True