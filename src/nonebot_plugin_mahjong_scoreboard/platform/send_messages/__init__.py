from typing import List

from nonebot import Bot
from nonebot.internal.adapter import Event

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
except ImportError:
    QQGuildBot = None

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
except ImportError:
    OneBotV11Bot = None


async def send_msgs(bot: Bot, event: Event, message: List[str]):
    if QQGuildBot is not None and isinstance(bot, QQGuildBot):
        for msg in message:
            await bot.send(event, msg)
    elif OneBotV11Bot is not None and isinstance(bot, OneBotV11Bot):
        from .onebot_v11 import send_msgs
        from nonebot.adapters.onebot.v11 import Message
        await send_msgs(bot, event, [Message(msg) for msg in message])
