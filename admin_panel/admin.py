from django.contrib import admin


# Register your models here.

class StaffAdminArea(admin.AdminSite):
    site_header = 'Super User Administration'


staff_site = StaffAdminArea(name='StaffAdmin')

