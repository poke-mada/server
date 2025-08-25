from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from admin_panel.admin import staff_site
from api.data_loader_view import LoadJsonDataView
from api.model_views.evolutions import EvolutionsUploadView
from api.views import FileUploadView, FileUploadManyView, LoadItemNamesView
from pokemada.views import overlay, showdown

urlpatterns = [
    path('admin/', admin.site.urls),
    path('staff/', staff_site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('user/', include('api_auth.urls')),
    path('api/', include('api.router')),
    path('overlay/<str:streamer_name>/', overlay),
    path('showdown/<str:streamer_name>/', showdown),
    path('upload_save/', FileUploadView.as_view()),
    path('load_data/', LoadJsonDataView.as_view()),
    path('upload_save_many/', FileUploadManyView.as_view()),
    path('load_evolutions/', EvolutionsUploadView.as_view()),
    path('load_item_names/', LoadItemNamesView.as_view()),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": 'statics/'}),
    path('_nested_admin/', include('nested_admin.urls')),
]
