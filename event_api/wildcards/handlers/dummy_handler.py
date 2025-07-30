from event_api.models import WildcardLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("dummy_handler", verbose='Dummy Handler')
class DummyHandler(BaseWildCardHandler):
    pass