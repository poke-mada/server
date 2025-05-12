from django.contrib import admin

from rewards_api.models import RewardBundle, PokemonReward, Reward, ItemReward, MoneyReward, WildcardReward
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin



class PokemonRewardAdmin(NestedTabularInline):
    min_num = 0
    extra = 0
    model = PokemonReward


class WildcardRewardAdmin(NestedTabularInline):
    model = WildcardReward
    min_num = 0
    extra = 0


class ItemRewardAdmin(NestedTabularInline):
    model = ItemReward
    min_num = 0
    extra = 0


class MoneyRewardAdmin(NestedTabularInline):
    model = MoneyReward
    min_num = 0
    extra = 0


class RewardInline(NestedTabularInline):
    model = Reward
    min_num = 1
    extra = 0
    inlines = [
        PokemonRewardAdmin,
        WildcardRewardAdmin,
        ItemRewardAdmin,
        MoneyRewardAdmin,
    ]


@admin.register(RewardBundle)
class RewardBundleAdmin(NestedModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]
