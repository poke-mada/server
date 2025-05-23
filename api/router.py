from django.urls import path, include
from rest_framework import routers

from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet, GameEventViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)
router.register(r'events', GameEventViewSet)


urlpatterns = [
    path('', include(router.urls))
]
