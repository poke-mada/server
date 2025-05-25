from django.urls import re_path
from websocket.sockets import MyConsumer, DataConsumer

websocket_urlpatterns = [
    re_path(r'ws/alerts/(?P<room_name>\w+)$', MyConsumer.as_asgi()),
    re_path(r'ws/data/(?P<room_name>\w+)$', DataConsumer.as_asgi()),
]
