from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models

from event_api.models import CoinTransaction, Wildcard, Streamer, StreamPlatformUrl, StreamerWildcardInventoryItem, \
    WildcardLog, ErrorLog, GameEvent, GameMod, MastersProfile
from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings, GiveMoneyHandlerSettings
from rewards_api.models import StreamerRewardInventory
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

import event_api.wildcards.handlers  # Replace with actual path
from event_api.wildcards import WildCardExecutorRegistry

# Register your models here.

admin.site.unregister(User)
admin.site.register(GameEvent)
admin.site.register(GameMod)


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


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'reason', 'amount', 'TYPE',)
    search_fields = ('trainer__name', 'TYPE')


@admin.register(WildcardLog)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'wildcard__name', 'details',)
    search_fields = ('trainer__name', 'wildcard__name')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'details', 'message',)
    search_fields = ('trainer__name',)


@admin.register(Wildcard)
class WildcardAdmin(admin.ModelAdmin):
    inlines_map = {
        'give_item': [GiveItemHandlerSettingsInline],
        'give_money': [GiveMoneyHandlerSettingsInline]
    }
    list_display = ('name', 'price', 'quality', 'is_active')
    search_fields = ('name', 'price', 'quality',)

    def get_inline_instances(self, request, obj=None):
        if obj and obj.handler_key in self.inlines_map:
            return [inline(self.model, self.admin_site) for inline in self.inlines_map[obj.handler_key]]
        return []

    def formfield_for_dbfield(self, db_field, *args, **kwargs):
        if db_field.name == "handler_key":
            choices = WildCardExecutorRegistry.registries()
            return forms.ChoiceField(choices=[('', '---------')] + choices, required=False)
        return super().formfield_for_dbfield(db_field, *args, **kwargs)


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


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy')


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    list_display = (
        'username',
        'masters_profile__trainer',
        'first_name', 'last_name',
        'is_staff'
    )
    inlines = [MastersProfileInline, StreamerProfileInline]


admin.site.register(User, UserProfileAdmin)
