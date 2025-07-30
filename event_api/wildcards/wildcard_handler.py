from abc import ABC, abstractmethod

from django.contrib.auth.models import User


class BaseWildCardHandler(ABC):

    def __init__(self, wildcard, user: User):
        self.wildcard = wildcard
        self.user = user

    def validate(self, context):
        return True

    @abstractmethod
    def execute(self, context):
        pass
