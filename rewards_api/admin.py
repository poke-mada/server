from django.contrib import admin

from rewards_api.models import RewardBundle, PokemonReward


# Register your models here.


@admin.register(RewardBundle)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(PokemonReward)
class PokemonRewardAdmin(admin.ModelAdmin):
    list_display = ('pokemon_pid',)
    readonly_fields = ('pokemon_pid',)
