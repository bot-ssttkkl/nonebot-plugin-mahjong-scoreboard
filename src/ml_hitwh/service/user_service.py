from sqlalchemy import select

from ml_hitwh.model.orm import SQLSession
from ml_hitwh.model.orm.user import UserOrm


async def get_user_by_binding_qq(binding_qq: int) -> UserOrm:
    async with SQLSession() as session:
        stmt = select(UserOrm).where(UserOrm.binding_qq == binding_qq).limit(1)
        user = (await session.execute(stmt)).one_or_none()
        if user is None:
            user = UserOrm(binding_qq=binding_qq)
            session.add(user)

        return user
