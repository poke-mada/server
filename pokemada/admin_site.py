from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class CustomAdminSite(AdminSite):
    site_header = "Admin"
    site_title = "Admin"
    index_title = "Panel"

    def has_permission(self, request):
        return (
                request.user.is_active
                and request.user.is_staff
                and request.user.is_superuser  # permiso extra
        )


class CustomAdminConfig(AdminConfig):
    default_site = "pokemada.admin_site.CustomAdminSite"
