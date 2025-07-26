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


class CoinsRewardDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('amount'):
                raise forms.ValidationError("Amount is required for coin rewards.")


class ItemRewardDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('item'):
                raise forms.ValidationError("Item is required for item rewards.")
            if not form.cleaned_data.get('amount'):
                raise forms.ValidationError("Amount is required for item rewards.")


class WildcardRewardDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('wildcard'):
                raise forms.ValidationError("Wildcard is required for item rewards.")
            if not form.cleaned_data.get('amount'):
                raise forms.ValidationError("Amount is required for item rewards.")


class PokemonRewardDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('pokemon_data'):
                raise forms.ValidationError("Pokemon Data is required for item rewards.")


class RewardInline(admin.TabularInline):
    model = Reward
    min_num = 1
    extra = 0
    sortable_by = ['reward_type']

    class Media:
        js = ('admin/js/reward_type_switcher.js',)


@admin.register(RewardBundle)
class RewardBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = [RewardInline]
