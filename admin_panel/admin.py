from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token

from event_api.admin import UserProfileAdmin


# Register your models here.

class StaffAdminArea(admin.AdminSite):
    site_header = 'Super User Administration'


staff_site = StaffAdminArea(name='StaffAdmin')

staff_site.register(Token)
staff_site.register(Group, GroupAdmin)

staff_site.register(User, UserProfileAdmin)
