from event_api.models import WildcardLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("reverse_handler", verbose='Reverse Handler')
class DummyHandler(BaseWildCardHandler):
    pass