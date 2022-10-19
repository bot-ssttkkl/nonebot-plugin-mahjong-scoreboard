from functools import wraps
from typing import Type

from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.internal.matcher import Matcher


def handle_interruption(matcher: Type[Matcher]):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            event = None
            for x in args:
                if isinstance(x, MessageEvent):
                    event = x
                    break
            if event is None:
                for x in kwargs.values():
                    if isinstance(x, MessageEvent):
                        event = x
                        break

            if event and event.get_plaintext() == '/q':
                await matcher.finish("中止流程")

            await func(*args, **kwargs)

        return wrapped_func

    return decorator
