from sqlalchemy import select

from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm


async def get_user_by_binding_qq(binding_qq: int) -> UserOrm:
    session = data_source.session()
    stmt = select(UserOrm).where(UserOrm.binding_qq == binding_qq).limit(1)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = UserOrm(binding_qq=binding_qq)
        session.add(user)
        await session.commit()

    return user
