from django.contrib import admin

from new_market.models import MarketBlockLog, BankPokemon, MarketCooldownLog, BankItem


# Register your models here.

@admin.register(MarketBlockLog)
class MarketBlockLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'dex_number', 'blocked_until')


@admin.register(MarketCooldownLog)
class MarketCooldownLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'dex_number', 'blocked_until')


@admin.register(BankPokemon)
class BankPokemonAdmin(admin.ModelAdmin):
    list_display = ('owner', 'species_name',)


@admin.register(BankItem)
class BankItemAdmin(admin.ModelAdmin):
    list_display = ('owner', 'item_name', 'quantity')
