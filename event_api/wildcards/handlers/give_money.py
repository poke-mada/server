import random

from event_api.models import CoinTransaction, ErrorLog
from event_api.wildcards.handlers.settings.models import GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("give_money", verbose='Give Money Handler')
class GiveMoneyHandler(BaseWildCardHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        amount = context.get('amount')
        for index in range(amount):
            money_quantity = random.randint(self.wildcard.give_random_money_settings.min_quantity, self.wildcard.give_random_money_settings.max_quantity)
            CoinTransaction.objects.create(
                profile=self.user.masters_profile,
                amount=money_quantity,
                TYPE=CoinTransaction.INPUT,
                reason=f'se uso la carta {self.wildcard.name} {amount} veces'
            )
        return True
