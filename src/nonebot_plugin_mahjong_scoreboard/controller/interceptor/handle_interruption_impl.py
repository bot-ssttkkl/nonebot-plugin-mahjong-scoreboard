from functools import wraps
from typing import Type

from nonebot.internal.matcher import Matcher, current_event


def handle_interruption(matcher: Type[Matcher]):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            event = current_event.get()
            if event and event.get_plaintext() == '/q':
                await matcher.finish("中止流程")

            await func(*args, **kwargs)

        return wrapped_func

    return decorator
