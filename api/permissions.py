from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission, DjangoModelPermissions


class IsRoot(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_superuser)


class IsTrainer(DjangoModelPermissions):
    def has_permission(self, request, view):
        from event_api.models import MastersProfile
        user: User = request.user
        has_coaching = user.masters_profile.profile_type == MastersProfile.COACH
        has_training = user.masters_profile.profile_type == MastersProfile.TRAINER
        has_sudo = request.user.is_superuser
        return has_sudo or has_training or has_coaching


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        from event_api.models import MastersProfile
        user: User = request.user
        has_coaching = user.masters_profile.profile_type == MastersProfile.COACH
        return request.user.is_superuser or has_coaching
