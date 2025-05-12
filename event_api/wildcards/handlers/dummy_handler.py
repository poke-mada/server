from event_api.models import WildcardLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("dummy_handler", verbose='Dummy Handler')
class DummyHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    def execute(self, context):
        amount = context.get('amount')
        WildcardLog.objects.create(wildcard=self.wildcard, trainer=self.trainer, details=f'{amount} carta/s {self.wildcard.name} usada')
