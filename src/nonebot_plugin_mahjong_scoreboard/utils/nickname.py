from typing import Optional

from nonebot import Bot
from ssttkkl_nonebot_utils.platform import platform_func

from nonebot_plugin_mahjong_scoreboard.model import PlatformId
from nonebot_plugin_mahjong_scoreboard.model.identity import convert_platform_id_to_session


async def get_user_nickname(bot: Bot, platform_user_id: PlatformId, platform_group_id: Optional[PlatformId]) -> str:
    session = convert_platform_id_to_session(bot, platform_user_id, platform_group_id)
    return await platform_func(bot).get_user_nickname(session)
