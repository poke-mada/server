from event_api.models import Wildcard


class WildCardExecutorRegistry:
    _registry = {}

    @classmethod
    def register(cls, handler_key, verbose=None):
        def decorator(handler_cls):
            cls._registry[handler_key] = {
                'verbose': verbose if verbose is not None else handler_key,
                'handler': handler_cls
            }
            return handler_cls

        return decorator

    @classmethod
    def get_executor(cls, type_name):
        executor = cls._registry.get(type_name)

        if executor:
            return executor['handler']

        return None

    @classmethod
    def registries(cls):
        return [(key, value['verbose']) for key, value in cls._registry.items()]


# Shortcut
get_executor = WildCardExecutorRegistry.get_executor
