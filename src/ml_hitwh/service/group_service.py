from sqlalchemy import select

from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.group import GroupOrm


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
