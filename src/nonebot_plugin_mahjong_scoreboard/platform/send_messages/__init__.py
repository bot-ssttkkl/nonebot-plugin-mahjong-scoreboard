from typing import List

from nonebot import Bot
from nonebot.internal.adapter import Event

from nonebot_plugin_mahjong_scoreboard.platform.func_registry import func

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
    from nonebot.adapters.qqguild import Adapter as QQGuildAdapter


    @func.register(QQGuildAdapter.get_name(), "send_msgs")
    async def send_msgs(bot: Bot, event: Event, message: List[str]):
        for msg in message:
            await bot.send(event, msg)

except ImportError:
    pass

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
    from nonebot.adapters.onebot.v11 import Message as OnebotV11Message
    from .onebot_v11 import send_msgs as send_msgs_onebot_v11


    @func.register(OneBotV11Adapter.get_name(), "send_msgs")
    async def send_msgs(bot: Bot, event: Event, message: List[str]):
        await send_msgs_onebot_v11(bot, event, [OnebotV11Message(msg) for msg in message])

except ImportError:
    pass
