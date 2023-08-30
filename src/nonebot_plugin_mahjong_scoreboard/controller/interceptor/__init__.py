from functools import wraps

from nonebot.internal.matcher import current_event, current_matcher


def handle_interruption():
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            event = current_event.get()
            matcher = current_matcher.get()
            if event and event.get_plaintext() == '/q':
                await matcher.finish("中止流程")

            return await func(*args, **kwargs)

        return wrapped_func

    return decorator
