from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings, GiveMoneyHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("give_game_money", verbose='Give Game Money Handler')
class GiveGameMoneyHandler(BaseWildCardHandler):
    admin_inline_model = GiveMoneyHandlerSettings  # a model with extra config

    def execute(self, context):
        amount = context.get('amount')
        settings: GiveItemHandlerSettings = self.wildcard.give_item_settings
        return {
            'command': "give_money",
            'data': {
                "quantity": settings.quantity * amount
            }
        }
