from django.urls import path, include
from rest_framework import routers

from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet, GameEventViewSet, NewsletterViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)
router.register(r'events', GameEventViewSet)
router.register(r'newsletter', NewsletterViewSet)


urlpatterns = [
    path('', include(router.urls))
]
