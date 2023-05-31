from os import PathLike
from typing import Union, AsyncIterable, Iterator

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot_plugin_gocqhttp_cross_machine_upload_file import upload_file as onebot_v11_upload_file

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
except ImportError:
    OneBotV11Bot = None


async def upload_file(bot: Bot, event: Event, filename: str,
                      data: Union[None, bytes, str,
                                  AsyncIterable[Union[str, bytes]],
                                  Iterator[Union[str, bytes]]] = None,
                      path: Union[None, str, PathLike[str]] = None):
    if isinstance(bot, OneBotV11Bot):
        return await onebot_v11_upload_file(bot, event, filename, data, path)
    else:
        raise RuntimeError(f"{bot.type} do not support upload file")


__all__ = ("upload_file",)
