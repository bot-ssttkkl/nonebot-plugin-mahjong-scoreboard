from nonebot.internal.matcher import current_bot

from .mapper import map_group
from ..config import conf
from ..model import Group
from ..model.identity import PlatformId
from ..platform import func
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
    return await func(bot).is_group_admin(bot,
                                          PlatformId.parse(user.platform_user_id),
                                          PlatformId.parse(group.platform_group_id))
