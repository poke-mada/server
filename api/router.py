from django.urls import path, include
from rest_framework import routers

from api.model_views.bank import BankViewSet
from api.model_views.market import MarketViewSet
from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet, GameEventViewSet, NewsletterViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)
router.register(r'events', GameEventViewSet)
router.register(r'newsletter', NewsletterViewSet)
router.register(r'market', MarketViewSet)
router.register(r'bank', BankViewSet)


urlpatterns = [
    path('', include(router.urls))
]
