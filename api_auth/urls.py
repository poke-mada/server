from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path, include

from api_auth import admin

urlpatterns = [
    path('login/', obtain_auth_token, name='login')
]
