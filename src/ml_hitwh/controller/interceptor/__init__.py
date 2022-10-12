from typing import Type

from nonebot.internal.matcher import Matcher

from .handle_error_impl import handle_error
from .session_scope_impl import session_scope


def general_interceptor(matcher: Type[Matcher]):
    def decorator(func):
        func = session_scope(matcher)(func)
        func = handle_error(matcher)(func)
        return func

    return decorator


__all__ = ("general_interceptor", )
