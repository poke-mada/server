from django.urls import path, include
from rest_framework import routers
from django.urls import re_path
from .sockets import MyConsumer

from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet, GameEventViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)
router.register(r'events', GameEventViewSet)

websocket_urlpatterns = [
    re_path(r'ws/alerts/$', MyConsumer.as_asgi()),
]

urlpatterns = [
    path('', include(router.urls))
]
