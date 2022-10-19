from typing import Type

from nonebot.internal.matcher import Matcher

from .handle_error_impl import handle_error
from .handle_interruption_impl import handle_interruption


def general_interceptor(matcher: Type[Matcher]):
    def decorator(func):
        func = handle_error(matcher)(func)
        return func

    return decorator


def workflow_interceptor(matcher: Type[Matcher]):
    def decorator(func):
        func = general_interceptor(matcher)(func)
        func = handle_interruption(matcher)(func)
        return func

    return decorator


__all__ = ("general_interceptor", "workflow_interceptor",)
