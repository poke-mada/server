from django.urls import path, include
from rest_framework import routers

from api.model_views.error import ErrorLogViewSet
from api.model_views.market import MarketViewSet
from api.model_views.notifications import ProfileNotificationViewSet
from api.model_views.rewards import RewardsViewSet
from api.model_views.roulette import RouletteViewSet
from api.model_views.segments import SegmentConfigurationViewSet
from api.views import TrainerViewSet, MoveViewSet, WildcardViewSet, GameEventViewSet, NewsletterViewSet

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'moves', MoveViewSet)
router.register(r'wildcards', WildcardViewSet)
router.register(r'events', GameEventViewSet)
router.register(r'newsletter', NewsletterViewSet)
router.register(r'market', MarketViewSet)
router.register(r'segment', SegmentConfigurationViewSet)
# router.register(r'bank', BankViewSet)
router.register(r'roulette', RouletteViewSet)
router.register(r'notifications', ProfileNotificationViewSet)
router.register(r'errors', ErrorLogViewSet)
router.register(r'rewards', RewardsViewSet)


urlpatterns = [
    path('', include(router.urls))
]
