from event_api.models import WildcardLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("alert_handler", verbose='Alert Handler')
class AlertHandler(BaseWildCardHandler):
    def validate(self, context):
        return

    def execute(self, context):
        pass
