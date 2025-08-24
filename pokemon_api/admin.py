from django.contrib import admin
from django import forms
from django.forms import modelformset_factory
from nested_admin.nested import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from pokemon_api import models
from pokemon_api.models import ContextLocalization, ItemNameLocalization

from admin_panel.admin import staff_site

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


@admin.register(models.Item, site=staff_site)
class ItemAdmin2(NestedModelAdmin):
    list_display = ('index', 'name', 'api_loaded')
    search_fields = ('index', 'name', 'localization')

    def has_module_permission(self, request):
        # Oculta el modelo del index del admin
        return False

    def has_view_permission(self, request, obj=None):
        # Permite acceder a la vista autocomplete
        return True


@admin.register(models.Type)
class TypeAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations',)
    list_display = ('index', 'name', 'localization')
    search_fields = ('index', 'name', 'localization')


@admin.register(models.ItemNameLocalization)
class NameLocalizationAdmiin(NestedModelAdmin):
    list_display = ('language', 'content')
    fields = ('language', 'content')


@admin.register(models.ContextLocalization)
class NameLocalizationAdmiin(NestedModelAdmin):
    list_display = ('language', 'content')
    fields = ('language', 'content')


@admin.register(models.PokemonNature)
class PokemonNatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'localization', 'stat_up', 'stat_down')
    search_fields = ('name', 'localization')
    autocomplete_fields = ('name_localizations',)


@admin.register(models.PokemonAbility)
class PokemonAbilityAdmin(admin.ModelAdmin):
    readonly_fields = ('name_localizations', 'flavor_text_localizations')
    list_display = ('index', 'name', 'localization')
    search_fields = ('index', 'name', 'localization')


@admin.register(models.Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('dex_number', 'form', 'name')
    search_fields = ('name', 'dex_number')
    # readonly_fields = ('dex_number', 'types', 'name', 'form')
