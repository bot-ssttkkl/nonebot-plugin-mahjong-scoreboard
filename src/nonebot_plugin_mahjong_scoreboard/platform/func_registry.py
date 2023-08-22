from functools import lru_cache
from typing import Callable, Mapping, Union, Optional

from nonebot import Bot


class UnsupportedBotError(RuntimeError):
    ...


class FuncRegistry:
    def __init__(self, func: Mapping[str, Callable]):
        self._func = func

    def __getattr__(self, item):
        if item in self._func:
            return self._func[item]
        else:
            raise UnsupportedBotError()


class FuncRegistryFactory:
    def __init__(self):
        self._registry = []

    def register(self, bot_type: str, func_name: str, func: Optional[Callable] = None):
        def decorator(func: Callable):
            self._registry.append((bot_type, func_name, func))
            return func

        if func is None:
            return decorator
        else:
            decorator(func)

    @lru_cache(maxsize=16)
    def __call__(self, bot: Union[str, Bot]) -> FuncRegistry:
        if isinstance(bot, Bot):
            bot_type = bot.type
        else:
            bot_type = bot

        func_mapping = {}
        for type_, name, func in self._registry:
            if bot_type == type_:
                func_mapping[name] = func
        return FuncRegistry(func_mapping)


func = FuncRegistryFactory()

__all__ = ("func", "FuncRegistry", "FuncRegistryFactory", "UnsupportedBotError")
