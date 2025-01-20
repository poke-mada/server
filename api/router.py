from django.urls import path, include
from rest_framework import routers

from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)


urlpatterns = [
    path('', include(router.urls))
]
