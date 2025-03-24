from django.contrib import admin

from rewards_api.models import RewardBundle, PokemonReward, Reward

# Register your models here.


class RewardInline(admin.TabularInline):
    model = Reward
    min_num = 1
    max_num = 4


@admin.register(RewardBundle)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]


@admin.register(PokemonReward)
class PokemonRewardAdmin(admin.ModelAdmin):
    list_display = ('pokemon_pid',)
    readonly_fields = ('pokemon_pid',)
