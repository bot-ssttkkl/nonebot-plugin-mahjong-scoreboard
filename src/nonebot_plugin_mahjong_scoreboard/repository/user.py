from sqlalchemy import select

from .base import Repository
from .data_model import UserOrm


class UserRepository(Repository[UserOrm]):
    Entity = UserOrm

    async def get(self, platform_user_id: str, *, insert_on_missing: bool = True) -> UserOrm:
        stmt = select(UserOrm).where(UserOrm.platform_user_id == platform_user_id).limit(1)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None and insert_on_missing:
            user = UserOrm(platform_user_id=platform_user_id)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user


__all__ = ("UserOrm",)
