from functools import wraps
from typing import Type

from nonebot import logger
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.exception import MatcherException
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError


def handle_error(matcher: Type[Matcher]):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MatcherException as e:
                raise e
            except BadRequestError as e:
                await matcher.finish(e.message)
            except ActionFailed as e:
                logger.exception(e)
                # 避免当发送消息错误时再尝试发送
                if e.info['msg'] != 'SEND_MSG_API_ERROR':
                    await matcher.finish(f"内部错误：{type(e)}{str(e)}")
            except Exception as e:
                logger.exception(e)
                await matcher.finish(f"内部错误：{type(e)}{str(e)}")

        return wrapped_func

    return decorator
