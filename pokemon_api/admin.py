from django.contrib import admin
from django import forms
from django.forms import modelformset_factory
from nested_admin.nested import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from pokemon_api import models
from pokemon_api.models import ContextLocalization, ItemNameLocalization

# Register your models here.
admin.site.register(models.MoveCategory)


@admin.register(models.Move)
class MoveAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations', 'flavor_text_localizations')
    list_display = ('index', 'name', 'move_type', 'power', 'accuracy')
    search_fields = ('index', 'name', 'move_type__name')


class NameLocalizationInline(NestedTabularInline):
    model = ItemNameLocalization
    fields = ('language', 'content')


@admin.register(models.Item)
class ItemAdmin(NestedModelAdmin):
    readonly_fields = ('flavor_text_localizations',)
    list_display = ('index', 'name', 'api_loaded')
    search_fields = ('index', 'name', 'localization')
    inlines = [NameLocalizationInline]


@admin.register(models.Type)
class TypeAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations',)
    list_display = ('index', 'name', 'localization')
    search_fields = ('index', 'name', 'localization')


@admin.register(models.PokemonNature)
class PokemonNatureAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations',)
    list_display = ('name', 'localization', 'stat_up', 'stat_down')
    search_fields = ('name', 'localization')


@admin.register(models.PokemonAbility)
class PokemonAbilityAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations', 'flavor_text_localizations')
    list_display = ('index', 'name', 'localization')
    search_fields = ('index', 'name', 'localization')


@admin.register(models.Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('dex_number', 'form', 'name')
    search_fields = ('name', 'dex_number')
    readonly_fields = ('dex_number', 'types', 'name', 'form')
