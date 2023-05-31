from typing import TypeVar, Generic, Optional

from sqlalchemy.ext.asyncio import AsyncSession

T_Entity = TypeVar("T_Entity")


class Repository(Generic[T_Entity]):
    Entity: T_Entity

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_pk(self, pk: any) -> Optional[T_Entity]:
        return await self.session.get(self.Entity, pk)
