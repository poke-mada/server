from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from event_api.models import CoinTransaction, Wildcard, Streamer, StreamPlatformUrl, StreamerWildcardInventoryItem, \
    CoachProfile, TrainerProfile, WildcardLog, ErrorLog, GameEvent, GameMod
from rewards_api.models import StreamerRewardInventory

# Register your models here.

admin.site.unregister(User)
admin.site.register(GameEvent)
admin.site.register(GameMod)


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'reason', 'amount', 'TYPE',)
    search_fields = ('trainer__name', 'TYPE')


@admin.register(WildcardLog)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'wildcard__name', 'details', )
    search_fields = ('trainer__name', 'wildcard__name')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'details', 'message', )
    search_fields = ('trainer__name',)


@admin.register(Wildcard)
class WildcardAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quality', 'is_active')
    search_fields = ('name', 'price', 'quality',)


class StreamPlatformInline(admin.TabularInline):
    model = StreamPlatformUrl
    min_num = 1


class WildcardInventoryItem(admin.TabularInline):
    model = StreamerWildcardInventoryItem
    min_num = 0


class RewardInventoryInline(admin.TabularInline):
    model = StreamerRewardInventory
    min_num = 0
    extra = 0


@admin.register(Streamer)
class StreamerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [StreamPlatformInline, WildcardInventoryItem, RewardInventoryInline]


class CoachProfileInline(admin.StackedInline):
    model = CoachProfile


class TrainerProfileInline(admin.StackedInline):
    model = TrainerProfile


class UserProfileAdmin(UserAdmin):
    list_display = ('username', 'trainer_profile__trainer', 'coaching_profile__coached_trainer', 'first_name', 'last_name', 'is_staff')
    inlines = [CoachProfileInline, TrainerProfileInline]


admin.site.register(User, UserProfileAdmin)
