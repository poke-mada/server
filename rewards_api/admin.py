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


class RewardInline(NestedTabularInline):
    model = Reward
    min_num = 1
    extra = 0
    show_change_link = True
    inlines = [ItemRewardAdmin, WildcardRewardAdmin, MoneyRewardAdmin, PokemonRewardAdmin]


@admin.register(RewardBundle)
class RewardBundleAdmin(NestedModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]
