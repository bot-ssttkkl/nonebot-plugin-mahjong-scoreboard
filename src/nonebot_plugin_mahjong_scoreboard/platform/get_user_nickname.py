from nonebot import Bot, logger
from nonebot.exception import ActionFailed

from nonebot_plugin_mahjong_scoreboard.model.platform_id import PlatformId

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
except ImportError:
    QQGuildBot = None

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
except ImportError:
    OneBotV11Bot = None


async def get_user_nickname(bot: Bot, platform_user_id: PlatformId, platform_group_id: PlatformId) -> str:
    user_id = platform_user_id.real_id
    group_id = platform_group_id.real_id

    try:
        if QQGuildBot is not None and isinstance(bot, QQGuildBot):
            guild_id, channel_id = group_id.split("_")
            member = await bot.get_member(guild_id=guild_id, user_id=user_id)

            return member.nick or user_id
        elif OneBotV11Bot is not None and isinstance(bot, OneBotV11Bot):
            user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            return user_info["card"] or user_info["nickname"]
    except ActionFailed as e:
        logger.warning(f"获取昵称失败, platform_user_id={platform_user_id}，platform_group_id={platform_group_id}，e={e}")
        return user_id
