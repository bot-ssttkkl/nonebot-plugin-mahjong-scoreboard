from functools import wraps
from typing import Type

from nonebot import logger
from nonebot.internal.matcher import Matcher

from ml_hitwh.errors import BadRequestError, ApiError


def handle_error(matcher: Type[Matcher]):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (BadRequestError, ApiError) as e:
                await matcher.finish(e.message)
            except Exception as e:
                await matcher.finish(f"内部错误：{type(e)}{str(e)}")
                logger.exception(e)

        return wrapped_func

    return decorator
