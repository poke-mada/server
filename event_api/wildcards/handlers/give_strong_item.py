from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler

available_items = [234, 281, 220, 287, 297, 270, 640, 272, 273, 639, 639, 639, 639, 275, 650, 269, 158]


@WildCardExecutorRegistry.register("strong_item", verbose='Give Strong Item Handler')
class GiveStrongItemHandler(BaseWildCardHandler):

    def validate(self, context, **kwargs):
        item_id = context.get('item_id')

        if item_id not in available_items:
            raise ValueError("non_mega_item")

        return True

    def execute(self, context):
        item_id = context.get('item_id')

        return {
            'command': "give_item",
            'data': {
                "item_id": item_id,
                "item_bag": 'items',
                "quantity": 1
            }
        }
