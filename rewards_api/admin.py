from django.contrib import admin
from django.core.handlers.asgi import ASGIRequest
from django.forms import forms
from django.forms.models import BaseInlineFormSet
from nested_admin.nested import NestedModelAdmin

from rewards_api.models import RewardBundle, Reward

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

    class Media:
        js = ('admin/js/reward_type_switcher.js',)


@admin.register(RewardBundle)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = (RewardInline,)
