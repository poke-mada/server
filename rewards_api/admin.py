from django.contrib import admin

from rewards_api.models import RewardBundle, PokemonReward, Reward, ItemReward, MoneyReward, WildcardReward
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin


class PokemonRewardAdmin(NestedTabularInline):
    model = PokemonReward
    min_num = 0
    max_num = 1


class WildcardRewardAdmin(NestedTabularInline):
    model = WildcardReward
    min_num = 0
    max_num = 1


class ItemRewardAdmin(NestedTabularInline):
    model = ItemReward
    min_num = 0
    max_num = 1


class MoneyRewardAdmin(NestedTabularInline):
    model = MoneyReward
    min_num = 0
    max_num = 1


class RewardInline(NestedStackedInline):
    model = Reward
    min_num = 1
    extra = 0


@admin.register(RewardBundle)
class RewardBundleAdmin(NestedModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]


@admin.register(Reward)
class RewardAdmin(NestedModelAdmin):
    min_num = 1
    extra = 0
    inlines = [ItemRewardAdmin, WildcardRewardAdmin, MoneyRewardAdmin, PokemonRewardAdmin]

    inlines_map = {
        'Item': [ItemRewardAdmin],
        'Wildcard': [WildcardRewardAdmin],
        'Money': [MoneyRewardAdmin],
        'Pokemon': [PokemonRewardAdmin]
    }

    def get_inline_instances(self, request, obj: Reward = None):
        if obj and obj.get_reward_type_display() in self.inlines_map:
            return [inline(self.model, self.admin_site) for inline in self.inlines_map[obj.get_reward_type_display()]]
        return []
