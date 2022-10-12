from functools import wraps
from typing import Type

from nonebot.internal.matcher import Matcher

from ml_hitwh.model.orm import data_source


def session_scope(matcher: Type[Matcher]):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            await func(*args, **kwargs)
            await data_source.remove_session()

        return wrapped_func

    return decorator
