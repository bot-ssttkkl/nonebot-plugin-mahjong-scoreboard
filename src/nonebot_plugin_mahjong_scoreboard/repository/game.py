from datetime import datetime, timedelta
from typing import Optional, Tuple, overload

from sqlalchemy import update, Select, select, func
from sqlalchemy.orm import selectinload

from .base import Repository
from .data_model import GameOrm, GameProgressOrm, GameRecordOrm
from .pagination import Page
from ..model.enums import GameState


class GameRepository(Repository[GameOrm]):
    async def get_by_pk(self, pk: int) -> Optional[GameOrm]:
        stmt = select(GameOrm).where(
            GameOrm.id == pk,
            GameOrm.accessible
        ).limit(1)
        season = (await self.session.execute(stmt)).scalar_one_or_none()
        return season

    @staticmethod
    def _build_game_query(stmt: Select,
                          *, offset: Optional[int] = None,
                          limit: Optional[int] = None,
                          uncompleted_only: bool = False,
                          completed_only: bool = False,
                          reverse_order: bool = False,
                          time_span: Optional[Tuple[datetime, datetime]] = None) -> Select:
        if uncompleted_only:
            stmt = stmt.where(GameOrm.state != GameState.completed)
        elif completed_only:
            stmt = stmt.where(GameOrm.state == GameState.completed)

        if reverse_order:
            stmt = stmt.order_by(GameOrm.id.desc())
        else:
            stmt = stmt.order_by(GameOrm.id)

        if time_span:
            stmt = stmt.where(GameOrm.create_time >= time_span[0])
            stmt = stmt.where(GameOrm.create_time < time_span[1])

        stmt = stmt.where(GameOrm.accessible)

        stmt = (stmt.offset(offset).limit(limit)
                .options(selectinload(GameOrm.records)))

        return stmt

    async def get_by_code(self, game_code: int, group_id: int) -> Optional[GameOrm]:
        stmt = select(GameOrm).where(
            GameOrm.group_id == group_id, GameOrm.code == game_code
        )
        stmt = self._build_game_query(stmt, limit=1)
        game = (await self.session.execute(stmt)).scalar_one_or_none()
        return game

    @overload
    async def get(self, group_id: Optional[int] = ...,
                  user_id: Optional[int] = ...,
                  season_id: Optional[int] = ...,
                  *, uncompleted_only: bool = False,
                  completed_only: bool = False,
                  offset: Optional[int] = None,
                  limit: Optional[int] = None,
                  reverse_order: bool = False,
                  time_span: Optional[Tuple[datetime, datetime]] = None) -> Page[GameOrm]:
        ...

    async def get(self, group_id: Optional[int] = None,
                  user_id: Optional[int] = None,
                  season_id: Optional[int] = None,
                  **kwargs) -> Page[GameOrm]:
        stmt = select(GameOrm, func.count(GameOrm.id).over().label("total"))

        if group_id is not None:
            stmt = stmt.where(GameOrm.group_id == group_id)

        if user_id is not None:
            stmt = stmt.join(GameRecordOrm).where(GameRecordOrm.user_id == user_id)

        if season_id is not None:
            stmt = stmt.where(GameOrm.season_id == season_id)

        stmt = self._build_game_query(stmt, **kwargs)

        result = (await self.session.execute(stmt)).all()

        if len(result) > 0:
            data = [row[0] for row in result]
            total = result[0][1]
            return Page(data=data, total=total)
        else:
            return Page(data=[], total=0)

    async def get_progress(self, game_id: int) -> Optional[GameProgressOrm]:
        return await self.session.get(GameProgressOrm, game_id)

    async def delete_all_uncompleted_game(self) -> int:
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        stmt = (update(GameOrm)
                .where(GameOrm.state != GameState.completed,
                       GameOrm.create_time < one_day_ago,
                       GameOrm.progress == None,
                       GameOrm.accessible)
                .values(accessible=False, delete_time=now, update_time=now)
                .execution_options(synchronize_session=False))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


__all__ = ("GameOrm",)
