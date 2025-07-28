from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

from admin_panel.models import InventoryGiftQuerySequence
from event_api.models import MastersProfile, MastersSegmentSettings, StreamerWildcardInventoryItem, ProfilePlatformUrl
from rewards_api.models import StreamerRewardInventory


# Register your models here.
class StaffAdminArea(admin.AdminSite):
    site_header = 'Super User Administration'


staff_site = StaffAdminArea(name='StaffAdmin')


@admin.action(description="Ejecutar Secuencia")
def run_sequence(modeladmin, request, queryset):
    for obj in queryset:
        obj.run()


@admin.register(InventoryGiftQuerySequence, site=staff_site)
class GiftSequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified', 'run_times')
    autocomplete_fields = ('targets',)
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
    fields = ('wildcard', 'quantity')
    model = StreamerWildcardInventoryItem
    min_num = 0
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
    extra = 0
    readonly_fields = ('is_current', 'community_pokemon_sprite')


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy')
    inlines = [MastersSegmentSettingsAdmin, ProfilePlatformUrlInline, WildcardInventoryItem, RewardInventoryInline]


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

    list_filter = ('masters_profile__is_pro', 'is_staff', 'masters_profile__profile_type')
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
