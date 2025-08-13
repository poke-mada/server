from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from nested_admin.nested import NestedStackedInline, NestedTabularInline, NestedModelAdmin

from admin_panel.models import InventoryGiftQuerySequence, DirectGiftQuerySequence, DirectGift
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
        obj.run()


@admin.register(InventoryGiftQuerySequence, site=staff_site)
class GiftSequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified', 'run_times')
    readonly_fields = ('created', 'modified', 'run_times')
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
    readonly_fields = ('platform', 'url')
    model = ProfilePlatformUrl
    min_num = 0
    max_num = 0
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
        return queryset.filter(is_current=True)


class MastersProfileInline(NestedStackedInline):
    model = MastersProfile
    readonly_fields = ('last_save_download', 'economy', 'rom_name', 'trainer',)
    inlines = [MastersSegmentSettingsAdmin, ProfilePlatformUrlInline, WildcardInventoryItem, RewardInventoryInline]


class UserProfileAdmin(NestedModelAdmin, UserAdmin):
    readonly_fields = (
        'groups', 'user_permissions', 'is_staff', 'is_superuser', 'first_name', 'last_name', 'email', 'last_login',
        'date_joined', 'username')
    list_display = (
        'username',
        'masters_profile__trainer',
        'profile_type',
        'is_tester',
        'is_pro',
        'is_active',
        'is_staff'
    )

    list_filter = ('masters_profile__is_pro', 'is_staff', 'masters_profile__is_tester')
    inlines = [MastersProfileInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(is_active=True, masters_profile__profile_type=MastersProfile.TRAINER)

    @admin.display(description='Profile Type', ordering='masters_profile__profile_type')
    def profile_type(self, obj):
        return obj.masters_profile.get_profile_type_display()

    @admin.display(description='Is Tester', boolean=True, ordering='masters_profile__is_tester')
    def is_tester(self, obj):
        return obj.masters_profile.is_tester

    @admin.display(description='Is Pro', boolean=True, ordering='masters_profile__is_pro')
    def is_pro(self, obj):
        return obj.masters_profile.is_pro


staff_site.register(User, UserProfileAdmin)
