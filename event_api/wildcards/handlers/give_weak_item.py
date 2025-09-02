from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler
from pokemon_api.models import Item

available_items = [541, 268, 219, 214, 271, 286, 221, 267, 542, 232, 295, 253, 265, 547, 230, 284, 285, 283, 282, 184, 189,
                   184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 686]


@WildCardExecutorRegistry.register("weak_item", verbose='Give Weak Item Handler')
class GiveWeakItemHandler(BaseWildCardHandler):

    def validate(self, context, **kwargs):
        item_id = context.get('item_id')

        if item_id not in available_items:
            raise ValueError("ESte objeto no es debil")

        return True

    def execute(self, context):
        item_id = context.get('item_id')
        item = Item.objects.get(pk=item_id)
        return {
            'command': "give_item",
            'data': {
                "item_id": item_id,
                "item_bag": item.item_bag,
                "quantity": 1
            }
        }
