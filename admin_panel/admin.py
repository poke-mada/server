from django.contrib import admin

from admin_panel.models import InventoryGiftQuerySequence
from event_api.models import MastersProfile


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
    search_fields = ('streamer_name',)

    def has_module_permission(self, request):
        # Oculta el modelo del index del admin
        return False

    def has_view_permission(self, request, obj=None):
        # Permite acceder a la vista autocomplete
        return True
