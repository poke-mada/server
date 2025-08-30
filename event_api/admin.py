from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Q
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

from admin_panel.admin import staff_site
from event_api.models import CoinTransaction, Wildcard, StreamerWildcardInventoryItem, \
    WildcardLog, ErrorLog, GameEvent, GameMod, MastersProfile, MastersSegmentSettings, DeathLog, ProfileImposterLog, \
    Imposter, ProfilePlatformUrl, Newsletter, BannedPokemon, Evolution, ProfileNotification, Sanction, \
    WildcardUpdateLog, SegmentConfiguration, StealLog, AlreadyCapturedLog
from event_api.wildcards import WildCardExecutorRegistry
from event_api.wildcards.handlers.settings.models import GiveItemHandlerSettings, GiveMoneyHandlerSettings, \
    GiveGameMoneyHandlerSettings, GiveRandomMoneyHandlerSettings, TimerHandlerSettings
from rewards_api.models import StreamerRewardInventory

# Register your models here.

admin.site.unregister(User)


@admin.action(description="Disable wildcards")
def disable_wildcards(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Enable wildcards")
def enable_wildcards(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Duplicar y banear")
def duplicate_and_ban(modeladmin, request, queryset):
    for log in queryset.all():  # type: DeathLog
        log.pk = None
        log.revived = False
        log.save()
        BannedPokemon.objects.create(profile=log.profile, species_name=log.species_name, dex_number=log.dex_number,
                                     reason=f'Se murió dos veces')


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


class StreamerFilter(admin.SimpleListFilter):
    title = "Streamer"
    parameter_name = "profile_id"

    def lookups(self, request, model_admin):
        # Traer solo perfiles con profile_type=TRAINER
        qs = (
            MastersProfile.objects
            .filter(profile_type=MastersProfile.TRAINER, transactions__isnull=False, is_tester=False)
            .values_list("id", "streamer_name")
            .distinct()
            .order_by("streamer_name")
        )

        # Devuelve lista de tuplas (valor, etiqueta)
        return list(qs)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(profile_id=self.value())
        return queryset


@admin.register(CoinTransaction, site=staff_site)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_on', 'profile__streamer_name', 'reason', 'amount', 'TYPE',)
    readonly_fields = ('created_on', 'profile', 'amount', 'reason', 'TYPE')
    search_fields = ('profile__streamer_name', 'TYPE', 'reason')
    list_filter = (StreamerFilter,)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WildcardLog, site=staff_site)
class WildcardLogAdmin(admin.ModelAdmin):
    list_display = ('profile__streamer_name', 'wildcard__name', 'details',)
    search_fields = ('profile__streamer_name', 'wildcard__name')
    list_filter = (StreamerFilter,)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('profile__streamer_name', 'message',)
    search_fields = ('profile__streamer_name',)
    list_filter = (StreamerFilter,)


@admin.register(DeathLog, site=staff_site)
class DeathLogAdmin(admin.ModelAdmin):
    list_display = ('profile__streamer_name', 'dex_number', 'species_name', 'mote', 'revived')
    search_fields = ('profile__streamer_name',)
    list_filter = (StreamerFilter,)
    readonly_fields = ('created_on', 'species_name')
    actions = [duplicate_and_ban]


@admin.register(BannedPokemon, site=staff_site)
class BannedPokemonAdmin(admin.ModelAdmin):
    list_display = ('profile__streamer_name', 'dex_number', 'species_name', 'reason')
    search_fields = ('profile__streamer_name',)
    list_filter = (StreamerFilter,)
    readonly_fields = ('species_name',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProfileImposterLog, site=staff_site)
class ProfileImposterLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'imposter', 'registered_amount', 'imposter__segment')
    search_fields = ('profile__streamer_name', 'imposter__message',)
    list_filter = (StreamerFilter,)
    autocomplete_fields = ('profile', 'imposter')


@admin.register(Imposter, site=staff_site)
class ImposterLogAdmin(admin.ModelAdmin):
    list_display = ('message', 'coin_reward', 'segment')
    search_fields = ('message', 'coin_reward', 'segment')


@admin.register(Wildcard, site=staff_site)
class WildcardStaff(admin.ModelAdmin):
    list_display = ('name', 'price', 'special_price', 'category', 'is_active', 'is_wip')
    search_fields = ('name', 'price', 'special_price', 'category',)
    readonly_fields = ('name', 'sprite', 'category', 'attack_level', 'handler_key', 'is_wip')
    list_filter = ('category', 'is_active', 'is_wip')
    actions = [disable_wildcards, enable_wildcards]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Wildcard)
class WildcardAdmin(admin.ModelAdmin):
    inlines_map = {
        'give_item': [GiveItemHandlerSettingsInline],
        'give_money': [GiveMoneyHandlerSettingsInline],
        'give_game_money': [GiveGameMoneyHandlerSettingsInline],
        'steal_money': [GiveMoneyHandlerSettingsInline],
        'release_pokemon': [GiveMoneyHandlerSettingsInline],
        'give_random_money': [GiveRandomMoneyHandlerSettingsInline],
        'release_shiny': [GiveMoneyHandlerSettingsInline],
        'timer_handler': [TimerHandlerSettingsInline],
    }
    list_display = ('name', 'price', 'category', 'is_active', 'is_wip')
    search_fields = ('name', 'price', 'category',)
    list_filter = ('category', 'is_active', 'is_wip')
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
    readonly_fields = (
        'platform',
        'url'
    )


class WildcardInventoryItem(NestedTabularInline):
    fields = ('wildcard', 'quantity')
    model = StreamerWildcardInventoryItem
    min_num = 0
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(wildcard__is_active=True, quantity__gt=0)


class RewardInventoryInline(NestedTabularInline):
    fields = ('reward', 'exchanges', 'is_available')
    readonly_fields = ('exchanges',)
    model = StreamerRewardInventory
    min_num = 0
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(reward__user_created=False, is_available=True)


class MastersSegmentSettingsInline(NestedStackedInline):
    model = MastersSegmentSettings
    min_num = 0
    extra = 0
    readonly_fields = ('is_current', 'community_pokemon_sprite')

    # def get_queryset(self, request):
    #     queryset = super().get_queryset(request)
    #     current = queryset.filter(is_current=True).first()
    #     return queryset.filter(Q(is_current=True) | Q(segment=current.segment - 1))


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy')
    inlines = [MastersSegmentSettingsInline, ProfilePlatformUrlInline, WildcardInventoryItem, RewardInventoryInline]


@admin.register(Newsletter, site=staff_site)
class NewsletterAdmin(NestedModelAdmin):
    readonly_fields = ('created_on',)
    list_display = ('created_on', 'message')
    autocomplete_fields = ('targets',)


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    list_display = (
        'username',
        'masters_profile__trainer',
        'profile_type',
        'is_tester',
        'is_pro',
        'is_active',
        'is_staff',
    )

    list_filter = ('masters_profile__is_pro', 'is_staff', 'masters_profile__profile_type', 'masters_profile__is_tester')
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


class GameModInline(admin.StackedInline):
    model = GameMod
    max_num = 1
    min_num = 0


@admin.register(GameEvent, site=staff_site)
class GameEventAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type', 'sub_type', 'available_date_from', 'available_date_to', 'free_join', 'force_available')
    list_filter = ('type', 'sub_type', 'free_join')
    inlines = [GameModInline]


@admin.register(Evolution)
class EvolutionAdmin(admin.ModelAdmin):
    list_display = ('dex_number', 'root_evolution')

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(ProfileNotification)
class EvolutionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'created_at', 'message')

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(Sanction, site=staff_site)
class SanctionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'created_at', 'message', 'money_substracted')
    autocomplete_fields = ('profile',)


admin.site.register(User, UserProfileAdmin)


@admin.register(WildcardUpdateLog)
class WildcardUpdateLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'message')
    readonly_fields = ('profile', 'message')


@admin.register(WildcardUpdateLog, site=staff_site)
class WildcardUpdateLogAdmin2(admin.ModelAdmin):
    list_display = ('profile', 'message')
    readonly_fields = ('profile', 'message')
    list_filter = (StreamerFilter,)

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(SegmentConfiguration)
class SegmentConfigurationAdmin(admin.ModelAdmin):
    list_display = ('segment', 'is_tournament', 'starts_at', 'ends_at')


@admin.register(SegmentConfiguration, site=staff_site)
class SegmentConfigurationAdmin2(admin.ModelAdmin):
    list_display = ('segment', 'is_tournament', 'starts_at', 'ends_at')


@admin.register(StealLog, site=staff_site)
class StealLogAdmin(admin.ModelAdmin):
    list_display = ('created_on', 'source', 'target', 'pokemon', 'bundle__name')

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(AlreadyCapturedLog)
class AlreadyCapturedLogAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'dex_number',
        'pid',
        'created_at',
    )

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False
