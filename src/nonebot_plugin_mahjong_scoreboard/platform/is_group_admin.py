from nonebot import Bot, logger
from nonebot.exception import ActionFailed

from nonebot_plugin_mahjong_scoreboard.utils.session import get_real_id

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
except ImportError:
    QQGuildBot = None

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
except ImportError:
    OneBotV11Bot = None


async def is_group_admin(bot: Bot, platform_user_id: str, platform_group_id: str) -> bool:
    user_id = get_real_id(platform_user_id)
    group_id = get_real_id(platform_group_id)

    try:
        if QQGuildBot is not None and isinstance(bot, QQGuildBot):
            guild_id, channel_id = group_id.split("_")
            perm = await bot.get_channel_permissions(channel_id=channel_id, user_id=user_id)
            perm = int(perm.permissions, 0)
            return bool(perm & 2)
        elif OneBotV11Bot is not None and isinstance(bot, OneBotV11Bot):
            member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            return member_info["role"] != "member"
    except ActionFailed as e:
        logger.warning(f"获取权限失败, platform_user_id={platform_user_id}，platform_group_id={platform_group_id}，e={e}")
        return False
