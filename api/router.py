from django.urls import path, include
from rest_framework import routers
from django.urls import re_path
from .sockets import MyConsumer

from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)

websocket_urlpatterns = [
    re_path(r'ws/trainer/$', MyConsumer.as_asgi()),
]

urlpatterns = [
    path('', include(router.urls))
]
