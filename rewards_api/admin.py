from django.contrib import admin

from rewards_api.models import RewardBundle, PokemonReward, Reward, ItemReward, MoneyReward, WildcardReward

# Register your models here.
admin.site.register(MoneyReward)
admin.site.register(ItemReward)
admin.site.register(WildcardReward)


class RewardInline(admin.TabularInline):
    model = Reward
    min_num = 1
    extra = 0


@admin.register(RewardBundle)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]


@admin.register(PokemonReward)
class PokemonRewardAdmin(admin.ModelAdmin):
    list_display = ('pokemon_pid',)
    readonly_fields = ('pokemon_pid',)
