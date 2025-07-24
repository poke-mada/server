from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models

from event_api.models import CoinTransaction, Wildcard, Streamer, StreamerWildcardInventoryItem, \
    WildcardLog, ErrorLog, GameEvent, GameMod, MastersProfile, MastersSegmentSettings, DeathLog, ProfileImposterLog, \
    Imposter, ProfilePlatformUrl, Newsletter
from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings, GiveMoneyHandlerSettings, \
    GiveGameMoneyHandlerSettings, GiveRandomMoneyHandlerSettings, TimerHandlerSettings
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
class GiveRandomMoneyHandlerSettingsInline(admin.StackedInline):
    model = GiveRandomMoneyHandlerSettings
    min_num = 1
    extra = 0


# admin.py
class GiveGameMoneyHandlerSettingsInline(admin.StackedInline):
    model = GiveGameMoneyHandlerSettings
    min_num = 1
    extra = 0


# admin.py
class TimerHandlerSettingsInline(admin.StackedInline):
    model = TimerHandlerSettings
    min_num = 1
    extra = 0


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_on', 'profile', 'reason', 'amount', 'TYPE',)
    readonly_fields = ('created_on',)
    search_fields = ('profile', 'TYPE')


@admin.register(WildcardLog)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__username', 'wildcard__name', 'details',)
    search_fields = ('profile__user__username', 'wildcard__name')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__username', 'details', 'message',)
    search_fields = ('profile__user__username',)


@admin.register(DeathLog)
class DeathLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__username', 'trainer__name', 'species_name', 'mote',)
    search_fields = ('profile__user__username', 'trainer__name',)


@admin.register(ProfileImposterLog)
class ProfileImposterLogAdmin(admin.ModelAdmin):
    list_display = ('profile__user__username', 'imposter__message',)
    search_fields = ('profile__user__username', 'imposter__message',)


@admin.register(Imposter)
class ImposterLogAdmin(admin.ModelAdmin):
    list_display = ('message', 'coin_reward')
    search_fields = ('message', 'coin_reward',)


@admin.register(Wildcard)
class WildcardAdmin(admin.ModelAdmin):
    inlines_map = {
        'give_item': [GiveItemHandlerSettingsInline],
        'give_money': [GiveMoneyHandlerSettingsInline],
        'give_game_money': [GiveGameMoneyHandlerSettingsInline],
        'steal_money': [GiveMoneyHandlerSettingsInline],
        'give_random_money': [GiveRandomMoneyHandlerSettingsInline],
        'timer_handler': [TimerHandlerSettingsInline],
    }
    list_display = ('name', 'price', 'category', 'is_active')
    search_fields = ('name', 'price', 'category',)
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


class WildcardInventoryItem(NestedTabularInline):
    fields = ('wildcard', 'quantity')
    model = StreamerWildcardInventoryItem
    min_num = 0
    extra = 0


class RewardInventoryInline(NestedTabularInline):
    fields = ('reward', 'exchanges', 'is_available')
    model = StreamerRewardInventory
    min_num = 0
    extra = 0


class MastersSegmentSettingsAdmin(NestedStackedInline):
    model = MastersSegmentSettings
    min_num = 0
    extra = 0
    readonly_fields = ('is_current', 'community_pokemon_sprite')


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy')
    inlines = [MastersSegmentSettingsAdmin, ProfilePlatformUrlInline, WildcardInventoryItem, RewardInventoryInline]


@admin.register(Newsletter)
class NewsletterAdmin(NestedModelAdmin):
    readonly_fields = ('created_on',)
    list_display = ('created_on', 'message')


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    list_display = (
        'username',
        'masters_profile__trainer',
        'profile_type',
        'is_tester',
        'is_pro',
        'is_active',
        'is_staff'
    )
    inlines = [MastersProfileInline]

    @admin.display(description='Profile Type', ordering='masters_profile__profile_type')
    def profile_type(self, obj):
        return obj.masters_profile.get_profile_type_display()

    @admin.display(description='Is Tester', boolean=True, ordering='masters_profile__is_tester')
    def is_tester(self, obj):
        return obj.masters_profile.is_tester

    @admin.display(description='Is Pro', boolean=True, ordering='masters_profile__is_pro')
    def is_pro(self, obj):
        return obj.masters_profile.is_pro


admin.site.register(User, UserProfileAdmin)
