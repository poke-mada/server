from django.urls import re_path
from websocket.sockets import MyConsumer

websocket_urlpatterns = [
    re_path(r'ws/alerts/(?P<room_name>\w+)$', MyConsumer.as_asgi()),
]
