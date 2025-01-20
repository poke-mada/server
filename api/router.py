from django.urls import path, include
from rest_framework import routers

from api.views import TrainerViewSet, MoveViewSet, TrainerView

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)


urlpatterns = [
    path('', include(router.urls))
]
