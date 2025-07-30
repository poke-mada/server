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
        if current_segment.karma < self.wildcard.karma_consumption:
            return 'No tienes suficiente karma'

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

    def execute(self, context):
        target_id = context.get('target_id')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)
        target_current_segment: MastersSegmentSettings = target_profile.current_segment_settings
        source_current_segment: MastersSegmentSettings = self.user.masters_profile.current_segment_settings

        target_current_segment.karma += self.wildcard.karma_consumption
        target_current_segment.steal_karma += self.wildcard.karma_consumption
        target_current_segment.attacks_received_left -= self.wildcard.karma_consumption
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

        return super().execute(context)
