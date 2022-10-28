from datetime import datetime
from operator import and_
from typing import Optional, List

from sqlalchemy.future import select
from sqlalchemy.sql.functions import count

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.enums import SeasonUserPointChangeType
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm, SeasonUserPointOrm, \
    SeasonUserPointChangeLogOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import is_group_admin


async def get_season_user_points(season: SeasonOrm) -> List[SeasonUserPointOrm]:
    session = data_source.session()

    stmt = select(SeasonUserPointOrm).where(
        SeasonUserPointOrm.season == season
    ).order_by(SeasonUserPointOrm.point.desc())
    sup = (await session.execute(stmt)).scalars().all()
    return sup


async def get_season_user_point_change_logs(season: SeasonOrm) -> List[SeasonUserPointChangeLogOrm]:
    session = data_source.session()

    stmt = select(SeasonUserPointChangeLogOrm).where(
        SeasonUserPointChangeLogOrm.season == season
    ).order_by(SeasonUserPointChangeLogOrm.create_time)
    logs = (await session.execute(stmt)).scalars().all()
    return logs


async def get_season_user_point(season: SeasonOrm, user: UserOrm) -> Optional[SeasonUserPointOrm]:
    session = data_source.session()

    stmt = select(SeasonUserPointOrm).where(
        SeasonUserPointOrm.season == season, SeasonUserPointOrm.user == user
    ).limit(1)
    sup: Optional[SeasonUserPointOrm] = (await session.execute(stmt)).scalar_one_or_none()
    return sup


async def get_season_user_point_rank(sup: SeasonUserPointOrm) -> int:
    session = data_source.session()
    stmt = select(count(SeasonUserPointOrm.user_id)).where(
        SeasonUserPointOrm.season_id == sup.season_id, SeasonUserPointOrm.point > sup.point
    )
    result = (await session.execute(stmt)).scalar_one_or_none()
    return result + 1


async def count_season_user_point(season: SeasonOrm) -> Optional[SeasonUserPointOrm]:
    session = data_source.session()

    stmt = select(count(SeasonUserPointOrm.user_id)).where(
        SeasonUserPointOrm.season == season
    )
    result = (await session.execute(stmt)).scalar_one_or_none()
    return result


async def change_season_user_point_manually(season: SeasonOrm,
                                            user: UserOrm,
                                            point: int,
                                            operator: UserOrm) -> SeasonUserPointOrm:
    session = data_source.session()
    group = await session.get(GroupOrm, season.group_id)
    if not await is_group_admin(operator, group):
        raise BadRequestError("没有权限")

    sup = await get_season_user_point(season, user)
    if sup is None:
        sup = SeasonUserPointOrm(season=season, user=user)
        session.add(sup)

    sup.point = point

    log = SeasonUserPointChangeLogOrm(season=season, user=user,
                                      change_type=SeasonUserPointChangeType.manually,
                                      change_point=point)
    session.add(log)

    sup.update_time = datetime.utcnow()
    await session.commit()
    return sup


async def change_season_user_point_by_game(game: GameOrm):
    session = data_source.session()

    for r in game.records:
        # 记录SeasonUserPoint
        stmt = select(SeasonUserPointOrm).where(
            SeasonUserPointOrm.season_id == game.season_id,
            SeasonUserPointOrm.user_id == r.user_id
        ).limit(1)
        user_point = (await session.execute(stmt)).scalar_one_or_none()

        if user_point is None:
            user_point = SeasonUserPointOrm(season_id=game.season_id, user_id=r.user_id, point=0)
            session.add(user_point)

        user_point.point += r.point

        # 记录SeasonUserPointChangeLog
        change_log = SeasonUserPointChangeLogOrm(user_id=r.user_id,
                                                 season_id=game.season_id,
                                                 change_type=SeasonUserPointChangeType.game,
                                                 change_point=r.point,
                                                 related_game_id=game.id)
        session.add(change_log)

    await session.commit()


async def revert_season_user_point_by_game(game: GameOrm):
    session = data_source.session()

    stmt = select(SeasonUserPointChangeLogOrm, SeasonUserPointOrm).join_from(
        SeasonUserPointChangeLogOrm, SeasonUserPointOrm, and_(
            SeasonUserPointChangeLogOrm.season_id == SeasonUserPointOrm.season_id,
            SeasonUserPointChangeLogOrm.user_id == SeasonUserPointOrm.user_id,
        )
    ).where(
        SeasonUserPointChangeLogOrm.related_game_id == game.id
    )

    for change_log, user_point in await session.execute(stmt):
        change_log: SeasonUserPointChangeLogOrm
        user_point: SeasonUserPointOrm

        user_point.point -= change_log.change_point

        await session.delete(change_log)

    await session.commit()
