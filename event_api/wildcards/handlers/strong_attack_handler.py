from .attack_handler import AttackHandler
from event_api.wildcards.registry import WildCardExecutorRegistry
from websocket.sockets import DataConsumer
from event_api.models import MastersProfile, MastersSegmentSettings


@WildCardExecutorRegistry.register("strong_attack", verbose='Strong Attack Handler')
class StrongAttackHandler(AttackHandler):

    def validate(self, context):
        from event_api.models import MastersProfile, Wildcard
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        current_segment: MastersSegmentSettings = self.user.masters_profile.current_segment_settings
        bypasses_reverse = context.get('bypasses_reverse', False)

        if current_segment.karma < self.wildcard.karma_consumption:
            return 'No tienes suficiente karma'

        if target_profile.has_shield():
            reverses = target_profile.wildcard_inventory.get(wildcard=Wildcard.objects.filter(handler_key='escudo_protector').first())
            reverses.quantity -= 1
            reverses.save()

            data = dict(
                user_name=self.user.masters_profile.streamer_name,
                wildcard=dict(
                    name=self.wildcard.name
                ),
                target_name=target_profile.streamer_name
            )
            DataConsumer.send_custom_data(target_profile.user.username, dict(
                type='shielded_attack_notification',
                data=data
            ))

            return '¡El objetivo se ha protegido!'

        if target_profile.has_reverse() and not bypasses_reverse:
            reverses = target_profile.wildcard_inventory.get(
                wildcard=Wildcard.objects.filter(handler_key='reverse_handler').first()
            )
            reverses.quantity -= 1
            reverses.save()

            data = dict(
                user_name=self.user.masters_profile.streamer_name,
                wildcard=dict(
                    name=self.wildcard.name
                ),
                target_name=target_profile.streamer_name
            )
            DataConsumer.send_custom_data(target_profile.user.username, dict(
                type='stolen_attack_notification',
                data=data
            ))

            return '¡El objetivo te ha robado la carta!'

        return super().validate(context)

    def execute(self, context, avoid_notification=False):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_current_segment = target_profile.current_segment_settings
        source_current_segment = self.user.masters_profile.current_segment_settings

        target_current_segment.steal_karma += self.wildcard.karma_consumption
        target_current_segment.attacks_received += self.wildcard.karma_consumption

        target_current_segment.karma += self.wildcard.karma_consumption
        target_current_segment.save()

        source_current_segment.karma -= self.wildcard.karma_consumption
        source_current_segment.save()

        DataConsumer.send_custom_data(self.user.username, dict(
            type='karma',
            data=str(source_current_segment.karma)
        ))

        DataConsumer.send_custom_data(target_profile.user.username, dict(
            type='karma',
            data=str(target_current_segment.karma)
        ))

        DataConsumer.send_custom_data(target_profile.user.username, dict(
            type='exp',
            data=str(target_current_segment.attacks_received)
        ))

        return super().execute(context, avoid_notification=avoid_notification)
