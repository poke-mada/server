from event_api.models import WildcardLog
from event_api.wildcards.registry import WildCardExecutorRegistry
from event_api.wildcards.wildcard_handler import BaseWildCardHandler


@WildCardExecutorRegistry.register("escudo_protector", verbose='Escudo Protector')
class ShieldHandler(BaseWildCardHandler):
    pass