from functools import wraps

from nonebot import logger
from nonebot.exception import MatcherException, ActionFailed
from nonebot.internal.matcher import current_event, current_matcher

from ...errors import BadRequestError, ResultError


def handle_error():
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            matcher = current_matcher.get()
            try:
                return await func(*args, **kwargs)
            except MatcherException as e:
                raise e
            except BadRequestError as e:
                await matcher.finish(f"{e.message}\n\n指令用法：{matcher.__help_info__}")
            except ResultError as e:
                await matcher.finish(e.message)
            except ActionFailed as e:
                # 避免当发送消息错误时再尝试发送
                logger.exception(e)
            except Exception as e:
                logger.exception(e)
                await matcher.finish(f"内部错误：{type(e)}{str(e)}")

        return wrapped_func

    return decorator


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
