import os
import django
from channels.routing import get_default_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.router import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pokemada.settings')
django.setup()
application = ProtocolTypeRouter({
    "http": get_default_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
