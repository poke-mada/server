from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from event_api.models import CoinTransaction, Wildcard, Streamer, StreamPlatformUrl, StreamerWildcardInventoryItem, \
    CoachProfile, TrainerProfile, WildcardLog

# Register your models here.

admin.site.unregister(User)


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'reason', 'amount', 'TYPE',)
    search_fields = ('trainer__name', 'TYPE')


@admin.register(WildcardLog)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('trainer__name', 'wildcard__name', 'details', )
    search_fields = ('trainer__name', 'wildcard__name')


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


@admin.register(Streamer)
class StreamerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [StreamPlatformInline, WildcardInventoryItem]


class CoachProfileInline(admin.StackedInline):
    model = CoachProfile


class TrainerProfileInline(admin.StackedInline):
    model = TrainerProfile


class UserProfileAdmin(UserAdmin):
    inlines = [CoachProfileInline, TrainerProfileInline]


admin.site.register(User, UserProfileAdmin)
