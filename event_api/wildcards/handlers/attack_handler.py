
from websocket.sockets import DataConsumer
from .alert_handler import AlertHandler


class AttackHandler(AlertHandler):

    def validate(self, context):
        from event_api.models import MastersProfile, Wildcard
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        if target_profile.has_shield():
            shields = target_profile.wildcard_inventory.get(
                wildcard=Wildcard.objects.filter(handler_key='escudo_protector').first())
            shields.quantity -= 1
            shields.save()
            data = dict(
                user_name=self.user.masters_profile.streamer_name,
                wildcard=dict(
                    name=self.wildcard.name
                ),
                target_name=target_profile.streamer_name
            )
            DataConsumer.send_custom_data(target_profile.user.username, dict(
                type='failed_attack_notification',
                data=data
            ))

            return 'El objetivo se ha protegido'

        return super().validate(context)
