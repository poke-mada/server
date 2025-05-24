"""
URL configuration for pokemada project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.template.defaulttags import url
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework_swagger.views import get_swagger_view

from api.data_loader_view import LoadJsonDataView
from api.views import FileUploadView, FileUploadManyView
from pokemada.views import pro_overlay, coach_overlay

schema_view = get_swagger_view(title='Pastebin API')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('user/', include('api_auth.urls')),
    path('api/', include('api.router')),
    path('coach_overlay/<str:streamer_name>/', coach_overlay),
    path('pro_overlay/<str:streamer_name>/', pro_overlay),
    path('upload_save/', FileUploadView.as_view()),
    path('load_data/', LoadJsonDataView.as_view()),
    path('upload_save_many/', FileUploadManyView.as_view()),
    path('docs/', schema_view),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": 'statics/'}),
    path('_nested_admin/', include('nested_admin.urls')),
]
