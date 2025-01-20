from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission


class IsRoot(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_superuser)


class IsTrainer(BasePermission):
    def has_permission(self, request, view):
        user: User = request.user
        return bool(user.trainer_profile)


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        user: User = request.user
        return bool(user.coaching_profile)
