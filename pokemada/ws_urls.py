from django.urls import re_path
from api.sockets import MyConsumer

websocket_urlpatterns = [
    re_path(r'ws/alerts/$', MyConsumer.as_asgi()),
]
