from event_api.models import CoinTransaction
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("give_money", verbose='Give Money Handler')
class GiveMoneyHandler(BaseWildCardHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        amount = context.get('amount')
        money_quantity = self.wildcard.give_money_settings.quantity
        CoinTransaction.objects.create(
            profile=self.user.masters_profile,
            amount=money_quantity * amount,
            TYPE=CoinTransaction.INPUT,
            segment=self.user.masters_profile.current_segment_settings.segment,
            reason=f'se uso la carta {self.wildcard.name} {amount} veces'
        )
        return True
