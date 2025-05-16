from event_api.models import WildcardLog
from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from pokemon_api.models import Item


@WildCardExecutorRegistry.register("give_item", verbose='Give Item Handler')
class GiveItemHandler(BaseWildCardHandler):
    admin_inline_model = GiveItemHandlerSettings  # a model with extra config

    def execute(self, context):
        amount = context.get('amount')
        settings: GiveItemHandlerSettings = self.wildcard.give_item_settings
        return {
            'command': "give_item",
            'data': {
                "item_id": settings.item_id.index,
                "item_bag": settings.item_bag,
                "quantity": settings.quantity * amount
            }
        }
