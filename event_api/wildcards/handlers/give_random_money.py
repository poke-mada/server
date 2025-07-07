import random

from event_api.models import CoinTransaction
from event_api.wildcards.handlers.settings.models import GiveRandomMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("give_random_money", verbose='Give Random Money Handler')
class GiveRandomMoneyHandler(BaseWildCardHandler):
    admin_inline_model = GiveRandomMoneyHandlerSettings  # a model with extra config

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
