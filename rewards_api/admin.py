from django.contrib import admin
from django.core.handlers.asgi import ASGIRequest
from django.forms import forms
from django.forms.models import BaseInlineFormSet
from nested_admin.nested import NestedModelAdmin

from admin_panel.admin import staff_site
from rewards_api.models import RewardBundle, Reward, RoulettePrice, Roulette

ITEM = 0
WILDCARD = 1
MONEY = 2
POKEMON = 3


class RewardInline(admin.TabularInline):
    model = Reward
    min_num = 1
    extra = 0
    readonly_fields = ('pokemon_pid',)
    sortable_by = ('reward_type',)
    autocomplete_fields = ('item', 'wildcard')

    class Media:
        js = ('admin/js/reward_type_switcher.js',)


@admin.register(RewardBundle, site=staff_site)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active',)
    fields = (
        'name',
        'is_active',
        'description',
        'sender',
        'type',
    )
    inlines = (RewardInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(user_created=False)


class RoulettePriceInline(admin.TabularInline):
    model = RoulettePrice
    min_num = 0
    extra = 0
    readonly_fields = ('id',)
    sortable_by = ('name',)
    autocomplete_fields = ('wildcard',)
    fields = (
        'id',
        'name',
        'wildcard',
        'quantity'
    )


@admin.register(Roulette, site=staff_site)
class RouletteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'has_file')
    inlines = (RoulettePriceInline,)

    @admin.display(description='Tiene Archivo', boolean=True)
    def has_file(self, obj: Roulette):
        if obj.file:
            return True
        return False
