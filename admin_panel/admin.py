from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

from admin_panel.models import InventoryGiftQuerySequence, DirectGiftQuerySequence, DirectGift, ShowdownToken, \
    BanPokemonSequence, InventoryGiftQuerySequenceLog, DirectGiftQuerySequenceLog, ExtractionPokemonProcess, \
    ExtractPokemonDataSequence
from event_api.models import MastersProfile, MastersSegmentSettings, StreamerWildcardInventoryItem, ProfilePlatformUrl
from rewards_api.models import StreamerRewardInventory


# Register your models here.
class StaffAdminArea(admin.AdminSite):
    site_header = 'Super User Administration'

    def has_permission(self, request):
        user: User = request.user
        # Ejemplo: permitir acceso si tiene un permiso concreto
        return request.user.is_superuser or (
                request.user.is_active and user.groups.filter(name='Site Administrator').exists())


staff_site = StaffAdminArea(name='StaffAdmin')


@admin.action(description="Entregar Paquete")
def run_sequence(modeladmin, request, queryset):
    for obj in queryset:
        obj.run(request.user.masters_profile)


class InventoryGiftQuerySequenceLogInline(NestedStackedInline):
    model = InventoryGiftQuerySequenceLog
    readonly_fields = ('sequence_name', 'performer', 'message')
    fields = ('sequence_name', 'performer', 'message')


@admin.register(InventoryGiftQuerySequence, site=staff_site)
class GiftSequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified', 'run_times')
    readonly_fields = ('created', 'modified', 'run_times')
    search_fields = ('name',)
    autocomplete_fields = ('targets',)
    actions = [run_sequence]


class DirectGiftInline(admin.TabularInline):
    model = DirectGift
    min_num = 1
    extra = 0
    sortable_by = ('type',)
    autocomplete_fields = ('wildcard',)

    class Media:
        js = ('admin/js/gift_type_switcher.js',)


class DirectGiftQuerySequenceLogInline(NestedStackedInline):
    model = DirectGiftQuerySequenceLog
    readonly_fields = ('sequence_name', 'performer', 'message')
    fields = ('sequence_name', 'performer', 'message')


@admin.register(DirectGiftQuerySequence, site=staff_site)
class GiftSequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified', 'run_times')
    readonly_fields = ('created', 'modified', 'run_times')
    autocomplete_fields = ('targets',)
    inlines = [DirectGiftInline]
    actions = [run_sequence]


@admin.register(MastersProfile, site=staff_site)
class MastersProfileAdmin(admin.ModelAdmin):
    search_fields = ('streamer_name', 'user__username')

    def has_module_permission(self, request):
        # Oculta el modelo del index del admin
        return False

    def has_view_permission(self, request, obj=None):
        # Permite acceder a la vista autocomplete
        return True


class ProfilePlatformUrlInline(NestedTabularInline):
    model = ProfilePlatformUrl
    min_num = 0
    extra = 0


class WildcardInventoryItem(NestedTabularInline):
    readonly_fields = ('wildcard', 'quantity')
    fields = ('wildcard', 'quantity')
    model = StreamerWildcardInventoryItem
    min_num = 0
    max_num = 0
    extra = 0


class RewardInventoryInline(NestedTabularInline):
    fields = ('reward', 'exchanges', 'is_available')
    readonly_fields = ('exchanges',)
    model = StreamerRewardInventory
    min_num = 0
    extra = 0


class MastersSegmentSettingsAdmin(NestedStackedInline):
    model = MastersSegmentSettings
    min_num = 0
    # max_num = 0 TODO: comentado hasta que el tramo se actualice solo
    extra = 0
    readonly_fields = ('is_current', 'community_pokemon_sprite', 'segment', 'community_skip_used_in')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        current = queryset.filter(is_current=True).first()
        return queryset.filter(is_current=True)


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy', 'rom_name', 'trainer', 'death_count_display_f')
    autocomplete_fields = ('coached', 'main_coach')
    inlines = [MastersSegmentSettingsAdmin, ProfilePlatformUrlInline]


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    readonly_fields = (
        'user_permissions', 'is_staff', 'is_superuser', 'first_name', 'last_name', 'email', 'last_login',
        'date_joined')

    list_display = (
        'username',
        'streamer_name',
        'current_segment',
        'league',
        'is_pro',
        'has_coach',
        'has_token',
        'has_starter'
    )

    list_filter = ('masters_profile__is_pro', 'is_staff', 'masters_profile__profile_type')
    inlines = [MastersProfileInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(is_active=True,
                               masters_profile__profile_type__in=[MastersProfile.TRAINER, MastersProfile.COACH],
                               masters_profile__is_tester=False)

    @admin.display(description='Nombre', ordering='masters_profile__streamer_name')
    def streamer_name(self, obj):
        return obj.masters_profile.streamer_name

    @admin.display(description='Tramo Actual')
    def current_segment(self, obj):
        if not obj.masters_profile.current_segment_settings:
            return '-'
        return obj.masters_profile.current_segment_settings.segment

    @admin.display(description='Liga Actual')
    def league(self, obj):
        profile: MastersProfile = obj.masters_profile
        if profile.profile_type != MastersProfile.TRAINER:
            return 'Es coach'
        if not profile.current_segment_settings:
            return '-'
        return profile.current_segment_settings.tournament_league

    @admin.display(description='Is Tester', boolean=True, ordering='masters_profile__is_tester')
    def is_tester(self, obj):
        return obj.masters_profile.is_tester

    @admin.display(description='Tiene Coach', boolean=True)
    def has_coach(self, obj):
        if obj.masters_profile.main_coach:
            return True
        return False

    @admin.display(description='Es Pro?', boolean=True, ordering='masters_profile__is_pro')
    def is_pro(self, obj):
        return obj.masters_profile.is_pro

    @admin.display(description='Tiene Token SD', boolean=True)
    def has_token(self, obj: User):
        return bool(obj.masters_profile.showdown_token)

    @admin.display(description='Tiene Starter Definido', boolean=True)
    def has_starter(self, obj: User):
        profile: MastersProfile = obj.masters_profile
        if profile.profile_type == MastersProfile.COACH:
            profile: MastersProfile = profile.coached
        if not profile:
            return False
        return bool(profile.starter_dex_number)


@admin.register(ShowdownToken, site=staff_site)
class ShowdownTokenAdmin(admin.ModelAdmin):
    list_display = ('username',)
    fields = ('username', 'token')


@admin.register(BanPokemonSequence, site=staff_site)
class BanPokemonSequenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'dex_number', 'reason',)
    autocomplete_fields = ('profile',)


class ExtractionPokemonProcessInline(admin.TabularInline):
    model = ExtractionPokemonProcess
    readonly_fields = ('pokemon_mote', 'enc_data')
    autocomplete_fields = ('target',)
    extra = 0
    min_num = 1


@admin.register(ExtractPokemonDataSequence, site=staff_site)
class ExtractPokemonDataSequenceAdmin(admin.ModelAdmin):
    list_display = ('target', 'created_at', 'last_ran_at')
    list_filter = ('target',)
    readonly_fields = ('created_at', 'last_ran_at')
    autocomplete_fields = ('target',)
    inlines = [ExtractionPokemonProcessInline]


staff_site.register(User, UserProfileAdmin)
