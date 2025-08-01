from event_api.models import CoinTransaction, MastersProfile
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from .attack_handler import AttackHandler


@WildCardExecutorRegistry.register("steal_money", verbose='Steal Money Handler')
class StealMoneyHandler(AttackHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        target_id = context.get('target_id')
        amount = context.get('amount')
        target_profile: MastersProfile = MastersProfile.objects.get(id=target_id)

        money_quantity = self.wildcard.give_money_settings.quantity
        if target_profile.economy < money_quantity:
            money_quantity = target_profile.economy
        CoinTransaction.objects.create(
            profile=target_profile,
            amount=money_quantity,
            TYPE=CoinTransaction.OUTPUT,
            reason=f'se uso la carta {self.wildcard.name} contra ti {amount} veces'
        )

        CoinTransaction.objects.create(
            profile=self.user.masters_profile,
            amount=money_quantity,
            TYPE=CoinTransaction.INPUT,
            reason=f'se uso la carta {self.wildcard.name} {amount} veces'
        )
        return super().execute(context)
