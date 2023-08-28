from datetime import datetime
from typing import Optional, List

from sqlalchemy import update, select, and_, delete, func
from sqlalchemy.sql.functions import count

from .base import Repository
from .data_model import GameOrm, SeasonOrm, SeasonUserPointOrm, SeasonUserPointChangeLogOrm
from ..errors import ResultError
from ..model import GameState, SeasonUserPointChangeType
from ..utils.rank import ranked


class SeasonRepository(Repository[SeasonOrm]):
    async def get_by_pk(self, pk: int) -> Optional[SeasonOrm]:
        stmt = select(SeasonOrm).where(
            SeasonOrm.id == pk,
            SeasonOrm.accessible
        ).limit(1)
        season = (await self.session.execute(stmt)).scalar_one_or_none()
        return season

    async def get_by_code(self, season_code: str, group_id: int) -> Optional[SeasonOrm]:
        stmt = select(SeasonOrm).where(
            SeasonOrm.group_id == group_id,
            SeasonOrm.code == season_code,
            SeasonOrm.accessible
        ).limit(1)
        season = (await self.session.execute(stmt)).scalar_one_or_none()
        return season

    async def get_group_seasons(self, group_id: int) -> List[SeasonOrm]:
        stmt = select(SeasonOrm).where(
            SeasonOrm.group_id == group_id,
            SeasonOrm.accessible
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result]

    async def delete_uncompleted_games(self, season_id: int) -> int:
        now = datetime.utcnow()
        stmt = (update(GameOrm)
                .where(GameOrm.season_id == season_id, GameOrm.state != GameState.completed, GameOrm.accessible)
                .values(accessible=False, delete_time=now, update_time=now)
                .execution_options(synchronize_session=False))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_season_user_point(self, season_id: int, user_id: int,
                                    *, insert_on_missing: bool = False) -> Optional[SeasonUserPointOrm]:
        stmt = select(SeasonUserPointOrm).where(
            SeasonUserPointOrm.season_id == season_id, SeasonUserPointOrm.user_id == user_id
        ).limit(1)
        sup = (await self.session.execute(stmt)).scalar_one_or_none()
        if sup is None and insert_on_missing:
            sup = SeasonUserPointOrm(season_id=season_id, user_id=user_id)
            self.session.add(sup)
            await self.session.commit()
        return sup

    async def get_season_user_point_rank(self, season_id: int, point: int) -> int:
        stmt = select(count(SeasonUserPointOrm.user_id)).where(
            SeasonUserPointOrm.season_id == season_id, SeasonUserPointOrm.point > point
        )
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        return result + 1

    async def count_season_user_point(self, season_id: int) -> Optional[SeasonUserPointOrm]:
        stmt = select(count(SeasonUserPointOrm.user_id)).where(
            SeasonUserPointOrm.season_id == season_id
        )
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        return result

    async def get_season_user_points(self, season_id: int) -> List[SeasonUserPointOrm]:
        stmt = select(SeasonUserPointOrm).where(
            SeasonUserPointOrm.season_id == season_id
        ).order_by(SeasonUserPointOrm.point.desc())
        sup = (await self.session.execute(stmt)).scalars().all()
        return sup

    async def get_season_user_point_change_logs(self, season_id: Optional[int] = None,
                                                user_id: Optional[int] = None) -> List[SeasonUserPointChangeLogOrm]:
        stmt = select(SeasonUserPointChangeLogOrm, func.count(SeasonUserPointChangeLogOrm.id).over().label("total"))

        if season_id is not None:
            stmt = stmt.where(SeasonUserPointChangeLogOrm.season_id == season_id)

        if user_id is not None:
            stmt = stmt.where(SeasonUserPointChangeLogOrm.user_id == user_id)

        result = (await self.session.execute(stmt)).all()
        data = [row[0] for row in result]
        return data

    async def change_season_user_point_manually(self, season_id: int,
                                                user_id: int,
                                                point: float) -> SeasonUserPointOrm:
        season = await self.get_by_pk(season_id)
        sup = await self.get_season_user_point(season_id, user_id, insert_on_missing=True)

        sup.point = int(point * (10 ** -season.config.point_precision))

        log = SeasonUserPointChangeLogOrm(season_id=season.id, user_id=user_id,
                                          change_type=SeasonUserPointChangeType.manually,
                                          change_point=point)
        self.session.add(log)

        sup.update_time = datetime.utcnow()
        await self.session.commit()

        return sup

    async def change_season_user_point_by_game(self, game: GameOrm):
        for rank, r in ranked(game.records, key=lambda r: r.raw_point, reverse=True):
            # 记录SeasonUserPoint
            stmt = select(SeasonUserPointOrm).where(
                SeasonUserPointOrm.season_id == game.season_id,
                SeasonUserPointOrm.user_id == r.user_id
            ).limit(1)
            user_point = (await self.session.execute(stmt)).scalar_one_or_none()

            if user_point is None:
                user_point = SeasonUserPointOrm(season_id=game.season_id,
                                                user_id=r.user_id,
                                                point=0)
                self.session.add(user_point)

            user_point.point += r.raw_point

            # 记录SeasonUserPointChangeLog
            change_log = SeasonUserPointChangeLogOrm(user_id=r.user_id,
                                                     season_id=game.season_id,
                                                     change_type=SeasonUserPointChangeType.game,
                                                     change_point=r.raw_point,
                                                     related_game_id=game.id)
            self.session.add(change_log)

        await self.session.commit()

    async def revert_season_user_point_by_game(self, game: GameOrm):
        stmt = select(SeasonUserPointChangeLogOrm, SeasonUserPointOrm).join_from(
            SeasonUserPointChangeLogOrm, SeasonUserPointOrm, and_(
                SeasonUserPointChangeLogOrm.season_id == SeasonUserPointOrm.season_id,
                SeasonUserPointChangeLogOrm.user_id == SeasonUserPointOrm.user_id,
            )
        ).where(
            SeasonUserPointChangeLogOrm.related_game_id == game.id
        )

        for change_log, user_point in await self.session.execute(stmt):
            # 判断在此之后是否还变动过PT
            stmt = select(func.count(SeasonUserPointChangeLogOrm.id)).where(
                SeasonUserPointChangeLogOrm.season_id == change_log.season_id,
                SeasonUserPointChangeLogOrm.user_id == change_log.user_id,
                SeasonUserPointChangeLogOrm.id > change_log.id
            )
            cnt = (await self.session.execute(stmt)).scalar_one()

            if cnt != 0:
                raise ResultError("撤销结算失败，在该对局之后该用户PT发生了改变")

            user_point.point -= change_log.change_point
            await self.session.delete(change_log)

            # 若用户只有这一次PT变动，则删除PT记录
            stmt = select(func.count(SeasonUserPointChangeLogOrm.id)).where(
                SeasonUserPointChangeLogOrm.season_id == user_point.season_id,
                SeasonUserPointChangeLogOrm.user_id == user_point.user_id,
            )
            cnt = (await self.session.execute(stmt)).scalar_one()

            if cnt == 0:
                await self.session.delete(user_point)

        await self.session.commit()

    async def reset_season_user_point(self, season_id: int, user_id: int):
        sup = await self.get_season_user_point(season_id, user_id)
        if sup is None:
            return

        stmt = delete(SeasonUserPointChangeLogOrm).where(
            SeasonUserPointChangeLogOrm.season_id == sup.season_id,
            SeasonUserPointChangeLogOrm.user_id == sup.user_id
        )
        await self.session.execute(stmt)

        await self.session.delete(sup)
        await self.session.commit()


__all__ = ("SeasonOrm", "SeasonUserPointOrm", "SeasonUserPointChangeLogOrm")
