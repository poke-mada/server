from django.contrib import admin
from pip._vendor.rich.box import Box

from admin_panel.admin import staff_site
from event_api.models import SaveFile
from .models import Trainer, TrainerPokemon, TrainerBox, TrainerTeam, TrainerBoxSlot


# Register your models here.


class TrainerTeamTab(admin.TabularInline):
    fields = ['version', 'team']
    readonly_fields = ('version', 'team')
    model = TrainerTeam
    max_num = 3


class SaveFileAdmin(admin.TabularInline):
    readonly_fields = ('file', 'created_on')
    max_num = 1
    model = SaveFile


class BoxSlotInline(admin.TabularInline):
    readonly_fields = ('slot', 'pokemon',)
    model = TrainerBoxSlot


class MoveLinear(admin.TabularInline):
    model = TrainerPokemon.moves.through
    max_num = 4


class TrainerPokemonLinear(admin.TabularInline):
    fields = (
        'id',
        'mega_ability',
        'mote',
        'pokemon',
        'moves',
        'held_item',
        'nature',
        'ability',
    )
    autocomplete_fields = ('mega_ability',)
    readonly_fields = (
        'id',
        'mote',
        'pokemon',
        'moves',
        'types',
        'held_item',
        'nature',
        'ability',
    )
    model = TrainerPokemon
    max_num = 6


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [SaveFileAdmin]


@admin.register(TrainerPokemon)
class TrainerPokemonAdmin(admin.ModelAdmin):
    readonly_fields = ('moves', 'types', 'suffix', 'enc_data')
    list_display = ('id', 'pokemon__dex_number', 'trainer__name', 'pokemon', 'mote', 'level')
    search_fields = ('pokemon__dex_number', 'pokemon__name', 'mote', 'trainer__name')
    list_filter = ('trainer__name',)
    inlines = [MoveLinear]


@admin.register(TrainerTeam)
class TrainerTeamAdmin(admin.ModelAdmin):
    list_display = ('trainer_old__name', 'version')
    search_fields = ('trainer_old__name', 'version')
    readonly_fields = ('version', 'trainer_old')
    inlines = [TrainerPokemonLinear]


@admin.register(TrainerBox)
class TrainerBoxAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'box_number')
    search_fields = ('trainer__name', 'box_number')
    inlines = [BoxSlotInline]
