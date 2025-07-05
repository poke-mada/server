from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models

from event_api.models import CoinTransaction, Wildcard, Streamer, StreamPlatformUrl, StreamerWildcardInventoryItem, \
    WildcardLog, ErrorLog, GameEvent, GameMod, MastersProfile, MastersSegmentSettings, DeathLog, ProfileImposterLog, \
    Imposter, ProfilePlatformUrl
from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings, GiveMoneyHandlerSettings, \
    GiveGameMoneyHandlerSettings
from rewards_api.models import StreamerRewardInventory
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

import event_api.wildcards.handlers  # Replace with actual path
from event_api.wildcards import WildCardExecutorRegistry

# Register your models here.

admin.site.unregister(User)
admin.site.register(GameEvent)
admin.site.register(GameMod)


@admin.action(description="Disable wildcards")
def disable_wildcards(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Enable wildcards")
def enable_wildcards(modeladmin, request, queryset):
    queryset.update(is_active=True)


# admin.py
class GiveItemHandlerSettingsInline(admin.StackedInline):
    model = GiveItemHandlerSettings
    min_num = 1
    extra = 0


# admin.py
class GiveMoneyHandlerSettingsInline(admin.StackedInline):
    model = GiveMoneyHandlerSettings
    min_num = 1
    extra = 0


# admin.py
class GiveGameMoneyHandlerSettingsInline(admin.StackedInline):
    model = GiveGameMoneyHandlerSettings
    min_num = 1
    extra = 0


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_on', 'profile', 'reason', 'amount', 'TYPE',)
    readonly_fields = ('created_on',)
    search_fields = ('profile', 'TYPE')


@admin.register(WildcardLog)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'wildcard__name', 'details',)
    search_fields = ('trainer__name', 'wildcard__name')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'details', 'message',)
    search_fields = ('trainer__name',)


@admin.register(DeathLog)
class DeathLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__streamer_profile__name', 'trainer__name', 'species_name', 'mote',)
    search_fields = ('profile__user__streamer_profile__name', 'trainer__name',)


@admin.register(ProfileImposterLog)
class ProfileImposterLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__streamer_profile__name', 'imposter__message',)
    search_fields = ('profile__user__streamer_profile__name', 'imposter__message',)


@admin.register(Imposter)
class ImposterLogAdmin(admin.ModelAdmin):
    list_display = ('message', 'coin_reward')
    search_fields = ('message', 'coin_reward',)


@admin.register(Wildcard)
class WildcardAdmin(admin.ModelAdmin):
    inlines_map = {
        'give_item': [GiveItemHandlerSettingsInline],
        'give_money': [GiveMoneyHandlerSettingsInline],
        'give_game_money': [GiveGameMoneyHandlerSettingsInline]
    }
    list_display = ('name', 'price', 'quality', 'is_active')
    search_fields = ('name', 'price', 'quality',)
    actions = [disable_wildcards, enable_wildcards]

    def get_inline_instances(self, request, obj=None):
        if obj and obj.handler_key in self.inlines_map:
            return [inline(self.model, self.admin_site) for inline in self.inlines_map[obj.handler_key]]
        return []

    def formfield_for_dbfield(self, db_field, *args, **kwargs):
        if db_field.name == "handler_key":
            choices = WildCardExecutorRegistry.registries()
            return forms.ChoiceField(choices=[('', '---------')] + choices, required=False)
        return super().formfield_for_dbfield(db_field, *args, **kwargs)


class ProfilePlatformUrlInline(NestedTabularInline):
    model = ProfilePlatformUrl
    min_num = 0
    extra = 0


class StreamPlatformInline(NestedTabularInline):
    model = StreamPlatformUrl
    min_num = 0
    extra = 0


class WildcardInventoryItem(NestedTabularInline):
    model = StreamerWildcardInventoryItem
    min_num = 0


class RewardInventoryInline(NestedTabularInline):
    model = StreamerRewardInventory
    min_num = 0
    extra = 0


class StreamerProfileInline(NestedStackedInline):
    model = Streamer
    inlines = [StreamPlatformInline, WildcardInventoryItem, RewardInventoryInline]


class MastersSegmentSettingsAdmin(NestedStackedInline):
    model = MastersSegmentSettings
    min_num = 0
    extra = 0
    readonly_fields = ('is_current', 'community_pokemon_sprite')


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy')
    inlines = [MastersSegmentSettingsAdmin, ProfilePlatformUrlInline]


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    list_display = (
        'username',
        'masters_profile__trainer',
        'first_name', 'last_name',
        'is_staff'
    )
    inlines = [MastersProfileInline, StreamerProfileInline]


admin.site.register(User, UserProfileAdmin)
