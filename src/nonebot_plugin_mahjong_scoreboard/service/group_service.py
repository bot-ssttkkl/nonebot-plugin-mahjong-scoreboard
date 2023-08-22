from nonebot.internal.matcher import current_bot

from .mapper import map_group
from ..config import conf
from ..model import Group
from ..model.platform_id import PlatformId
from ..platform.is_group_admin import is_group_admin as platform_is_group_admin
from ..repository import data_source
from ..repository.data_model import GroupOrm
from ..repository.group import GroupRepository
from ..repository.user import UserOrm


async def get_group(platform_group_id: PlatformId) -> Group:
    session = data_source.session()
    repo = GroupRepository(session)
    group = await repo.get(str(platform_group_id))
    return await map_group(group, session)


async def is_group_admin(user_id: int, group_id: int) -> bool:
    if not conf.mahjong_scoreboard_enable_permission_check:
        return True

    session = data_source.session()
    user = await session.get(UserOrm, user_id)
    group = await session.get(GroupOrm, group_id)

    bot = current_bot.get()
    return await platform_is_group_admin(bot, user.platform_user_id, group.platform_group_id)
