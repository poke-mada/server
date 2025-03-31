from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission


class IsRoot(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_superuser)


class IsTrainer(BasePermission):
    def has_permission(self, request, view):
        user: User = request.user
        has_coaching = hasattr(user, 'coaching_profile')
        has_training = hasattr(user, 'trainer_profile')
        has_sudo = request.user.is_superuser
        print(has_coaching, has_training, has_sudo)
        return has_sudo or has_training or has_coaching


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        user: User = request.user
        return request.user.is_superuser or (
                    hasattr(user, 'coaching_profile') and bool(user.coaching_profile.coached_trainer))
