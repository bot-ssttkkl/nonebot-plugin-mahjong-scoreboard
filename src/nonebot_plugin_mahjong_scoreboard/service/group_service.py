from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.internal.matcher import current_bot
from sqlalchemy import select

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm


async def get_group_by_binding_qq(binding_qq: int) -> GroupOrm:
    session = data_source.session()
    stmt = select(GroupOrm).where(GroupOrm.binding_qq == binding_qq).limit(1)
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()
    if group is None:
        group = GroupOrm(binding_qq=binding_qq)
        session.add(group)
        await session.commit()

    return group


async def is_group_admin(user: UserOrm, group: GroupOrm) -> bool:
    bot = current_bot.get()
    member_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
    return member_info["role"] != "member"


async def ensure_group_admin(user: UserOrm, group: GroupOrm):
    if not await is_group_admin(user, group):
        raise BadRequestError("没有权限")


async def get_user_nickname(user: UserOrm, group: GroupOrm) -> str:
    bot = current_bot.get()
    try:
        user_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
        return user_info["card"] or user_info["nickname"]
    except ActionFailed as e:
        raise RuntimeError(e.info["wording"])
