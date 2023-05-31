from typing import Optional

from sqlalchemy import select

from .base import Repository
from .data_model import GroupOrm


class GroupRepository(Repository[GroupOrm]):
    Entity = GroupOrm

    async def get(self, platform_group_id: str, *, insert_on_missing: bool = True) -> Optional[GroupOrm]:
        stmt = select(GroupOrm).where(GroupOrm.platform_group_id == platform_group_id).limit(1)
        result = await self.session.execute(stmt)
        group = result.scalar_one_or_none()
        if group is None and insert_on_missing:
            group = GroupOrm(platform_group_id=platform_group_id)
            self.session.add(group)
            await self.session.commit()
            await self.session.refresh(group)

        return group


__all__ = ("GroupOrm",)
