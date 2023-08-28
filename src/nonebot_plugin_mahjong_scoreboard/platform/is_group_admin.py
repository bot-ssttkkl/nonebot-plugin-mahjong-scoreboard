from .func_registry import func
from ..model.identity import PlatformId

try:
    from nonebot.adapters.qqguild import Bot as QQGuildBot
    from nonebot.adapters.qqguild import Adapter as QQGuildAdapter


    @func.register(QQGuildAdapter.get_name(), "is_group_admin")
    async def is_group_admin(bot: QQGuildBot, platform_user_id: PlatformId, platform_group_id: PlatformId) -> bool:
        user_id = platform_user_id.real_id
        group_id = platform_group_id.real_id

        guild_id, channel_id = group_id.split("_")
        perm = await bot.get_channel_permissions(channel_id=channel_id, user_id=user_id)
        perm = int(perm.permissions, 0)
        return bool(perm & 2)

except ImportError:
    pass

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


    @func.register(OneBotV11Adapter.get_name(), "is_group_admin")
    async def is_group_admin(bot: OneBotV11Bot, platform_user_id: PlatformId, platform_group_id: PlatformId) -> bool:
        user_id = platform_user_id.real_id
        group_id = platform_group_id.real_id

        member_info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
        return member_info["role"] != "member"

except ImportError:
    pass
