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
from django.contrib import admin
from django.urls import path, include
from rest_framework_swagger.views import get_swagger_view

from api.data_loader_view import LoadJsonDataView
from api.views import FileUploadView, TrainerView, FileUploadManyView, TrainerSaveView

schema_view = get_swagger_view(title='Pastebin API')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('user/', include('api_auth.urls')),
    path('api/', include('api.router')),
    path('upload_save/', FileUploadView.as_view()),
    path('load_data/', LoadJsonDataView.as_view()),
    path('upload_save_many/', FileUploadManyView.as_view()),
    path('trainer/<str:trainer_name>/', TrainerView.as_view()),
    path('last_save/<str:trainer_name>/', TrainerSaveView.as_view()),
    path('docs/', schema_view)
]
