from django.urls import re_path
from websocket.sockets import OverlayConsumer, DataConsumer

websocket_urlpatterns = [
    re_path(r'ws/overlay/(?P<room_name>\w+)$', OverlayConsumer.as_asgi()),
    re_path(r'ws/data/(?P<room_name>\w+)$', DataConsumer.as_asgi()),
]
