from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler

mega_stones = [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 656, 657, 658, 659, 660, 661, 662,
               663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683,
               684, 685]


@WildCardExecutorRegistry.register("mega_item", verbose='Give Mega Stone Handler')
class GiveMegaItemHandler(BaseWildCardHandler):

    def validate(self, context, **kwargs):
        item_id = context.get('item_id')

        if item_id not in mega_stones:
            return "Esta no es una megapiedra"

        return super().validate(context)

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
