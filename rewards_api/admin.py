from django.contrib import admin
from django.core.handlers.asgi import ASGIRequest
from django.forms import forms
from django.forms.models import BaseInlineFormSet
from nested_admin.nested import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from admin_panel.admin import staff_site
from rewards_api.models import RewardBundle, Reward, RoulettePrice, Roulette, RouletteRollHistory, RoulettePriceWildcard

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


class RoulettePriceWildcardInline(NestedTabularInline):
    model = RoulettePriceWildcard
    min_num = 1
    max_num = 2
    extra = 0
    sortable_by = ('name',)
    fields = (
        'wildcard',
        'quantity'
    )


class RoulettePriceInline(NestedTabularInline):
    model = RoulettePrice
    min_num = 0
    extra = 0
    readonly_fields = ('id',)
    fields = (
        'name',
        'weight',
        'is_jackpot',
        'image',
    )
    inlines = (RoulettePriceWildcardInline,)


@admin.register(Roulette, site=staff_site)
class RouletteAdmin(NestedModelAdmin):
    list_display = ('id', 'name', 'segment', 'order', 'has_file')
    inlines = (RoulettePriceInline,)
    autocomplete_fields = ('wildcard',)

    @admin.display(description='Tiene Archivo', boolean=True)
    def has_file(self, obj: Roulette):
        if obj.file:
            return True
        return False


@admin.register(RouletteRollHistory, site=staff_site)
class RouletteRollHistoryAdminStaff(admin.ModelAdmin):
    list_display = (
        'profile',
        'roulette',
        'message',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RouletteRollHistory)
class RouletteRollHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'roulette',
        'message',
        'created_at',
    )