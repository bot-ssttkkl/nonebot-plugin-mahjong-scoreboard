from sqlalchemy import select

from ml_hitwh.model.orm import SQLSession
from ml_hitwh.model.orm.group import GroupOrm


async def get_group_by_binding_qq(binding_qq: int) -> GroupOrm:
    async with SQLSession() as session:
        stmt = select(GroupOrm).where(GroupOrm.binding_qq == binding_qq).limit(1)
        group = (await session.execute(stmt)).one_or_none()
        if group is None:
            group = GroupOrm(binding_qq=binding_qq)
            session.add(group)

        return group
