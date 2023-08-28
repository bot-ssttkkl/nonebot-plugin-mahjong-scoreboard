from .func_registry import func
from ..model.identity import PlatformId

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
    from nonebot.adapters.qqguild import Adapter as QQGuildAdapter


    @func.register(QQGuildAdapter.get_name(), "get_user_nickname")
    async def get_user_nickname(bot: QQGuildBot, platform_user_id: PlatformId, platform_group_id: PlatformId) -> str:
        user_id = platform_user_id.real_id
        group_id = platform_group_id.real_id

        guild_id, channel_id = group_id.split("_")
        member = await bot.get_member(guild_id=guild_id, user_id=user_id)

        return member.nick or user_id

except ImportError:
    pass

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


    @func.register(OneBotV11Adapter.get_name(), "get_user_nickname")
    async def get_user_nickname(bot: OneBotV11Bot, platform_user_id: PlatformId, platform_group_id: PlatformId) -> str:
        user_id = platform_user_id.real_id
        group_id = platform_group_id.real_id

        user_info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
        return user_info["card"] or user_info["nickname"]
except ImportError:
    pass
