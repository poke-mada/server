from abc import ABC, abstractmethod


class BaseWildCardHandler(ABC):

    def __init__(self, wildcard, trainer):
        self.wildcard = wildcard
        self.trainer = trainer

    def validate(self, context):
        pass

    @abstractmethod
    def execute(self, context):
        pass
