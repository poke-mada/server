from event_api.wildcards.handlers.settings.models import GiveGameMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("give_game_money", verbose='Give Game Money Handler')
class GiveGameMoneyHandler(BaseWildCardHandler):
    admin_inline_model = GiveGameMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        amount = context.get('amount')
        settings: GiveGameMoneyHandlerSettings = self.wildcard.give_game_money_settings
        return {
            'command': "give_money",
            'data': {
                "quantity": settings.quantity * amount
            }
        }
