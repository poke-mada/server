from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler

available_items = [541, 268, 219, 214, 271, 286, 221, 267, 542, 232, 295, 253, 265, 547, 275, 284, 285, 283, 282]


@WildCardExecutorRegistry.register("weak_item", verbose='Give Weak Item Handler')
class GiveWeakItemHandler(BaseWildCardHandler):

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
