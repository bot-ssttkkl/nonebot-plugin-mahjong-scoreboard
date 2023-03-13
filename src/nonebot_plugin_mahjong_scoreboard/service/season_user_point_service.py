from datetime import datetime
from operator import and_
from typing import Optional, List, Literal, overload, Tuple, Union

from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.sql.functions import count, func

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.enums import SeasonUserPointChangeType
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm, GameRecordOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm, SeasonUserPointOrm, \
    SeasonUserPointChangeLogOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import is_group_admin
from nonebot_plugin_mahjong_scoreboard.utils.rank import ranked


async def get_season_user_points(season: SeasonOrm) -> List[SeasonUserPointOrm]:
    session = data_source.session()

    stmt = select(SeasonUserPointOrm).where(
        SeasonUserPointOrm.season == season
    ).order_by(SeasonUserPointOrm.point.desc())
    sup = (await session.execute(stmt)).scalars().all()
    return sup


@overload
async def get_season_user_point_change_logs(season: Optional[SeasonOrm],
                                            user: Optional[UserOrm] = ...,
                                            *, offset: Optional[int] = ...,
                                            limit: Optional[int] = ...,
                                            reverse_order: bool = ...,
                                            join_game_and_record: Literal[False] = ...) \
        -> List[SeasonUserPointChangeLogOrm]:
    ...


@overload
async def get_season_user_point_change_logs(season: Optional[SeasonOrm],
                                            user: Optional[UserOrm] = ...,
                                            *, offset: Optional[int] = ...,
                                            limit: Optional[int] = ...,
                                            reverse_order: bool = ...,
                                            join_game_and_record: Literal[True] = ...) \
        -> List[Tuple[SeasonUserPointChangeLogOrm, GameOrm, GameRecordOrm]]:
    ...


async def get_season_user_point_change_logs(season: Optional[SeasonOrm] = None,
                                            user: Optional[UserOrm] = None,
                                            *, offset: Optional[int] = None,
                                            limit: Optional[int] = None,
                                            reverse_order: bool = False,
                                            join_game_and_record: bool = False) \
        -> Union[List[SeasonUserPointChangeLogOrm], List[Tuple[SeasonUserPointChangeLogOrm, GameOrm, GameRecordOrm]]]:
    session = data_source.session()

    if not join_game_and_record:
        stmt = select(SeasonUserPointChangeLogOrm)
    else:
        stmt = (select(SeasonUserPointChangeLogOrm, GameOrm, GameRecordOrm)
                .join_from(SeasonUserPointChangeLogOrm, GameOrm,
                           SeasonUserPointChangeLogOrm.related_game_id == GameOrm.id)
                .join_from(SeasonUserPointChangeLogOrm, GameRecordOrm,
                           and_(
                               SeasonUserPointChangeLogOrm.related_game_id == GameRecordOrm.game_id,
                               SeasonUserPointChangeLogOrm.user_id == GameRecordOrm.user_id
                           )))

    if season is not None:
        stmt = stmt.where(SeasonUserPointChangeLogOrm.season == season)

    if user is not None:
        stmt = stmt.where(SeasonUserPointChangeLogOrm.user == user)

    if reverse_order:
        stmt = stmt.order_by(SeasonUserPointChangeLogOrm.id.desc())
    else:
        stmt = stmt.order_by(SeasonUserPointChangeLogOrm.id)

    stmt = stmt.offset(offset).limit(limit)

    result = (await session.execute(stmt)).all()
    if join_game_and_record:
        return [(a, b, c) for (a, b, c) in result]
    else:
        return [x for (x,) in result]


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


async def reset_season_user_point(season: SeasonOrm,
                                  user: UserOrm,
                                  operator: UserOrm):
    session = data_source.session()

    group = await session.get(GroupOrm, season.group_id)
    if not await is_group_admin(operator, group):
        raise BadRequestError("没有权限")

    sup = await get_season_user_point(season, user)
    if sup is None:
        return

    stmt = delete(SeasonUserPointChangeLogOrm).where(
        SeasonUserPointChangeLogOrm.season_id == sup.season_id,
        SeasonUserPointChangeLogOrm.user_id == sup.user_id
    )
    await session.execute(stmt)

    await session.delete(sup)
    await session.commit()


async def change_season_user_point_manually(season: SeasonOrm,
                                            user: UserOrm,
                                            point: float,
                                            operator: UserOrm) -> SeasonUserPointOrm:
    session = data_source.session()
    group = await session.get(GroupOrm, season.group_id)
    if not await is_group_admin(operator, group):
        raise BadRequestError("没有权限")

    sup = await get_season_user_point(season, user)
    if sup is None:
        sup = SeasonUserPointOrm(season=season, user=user)
        session.add(sup)

    sup.point = int(point * (10 ** -season.config.point_precision))

    log = SeasonUserPointChangeLogOrm(season=season, user=user,
                                      change_type=SeasonUserPointChangeType.manually,
                                      change_point=point)
    session.add(log)

    sup.update_time = datetime.utcnow()
    await session.commit()
    return sup


async def change_season_user_point_by_game(game: GameOrm):
    session = data_source.session()

    for rank, r in ranked(game.records, key=lambda r: r.raw_point, reverse=True):
        # 记录SeasonUserPoint
        stmt = select(SeasonUserPointOrm).where(
            SeasonUserPointOrm.season_id == game.season_id,
            SeasonUserPointOrm.user_id == r.user_id
        ).limit(1)
        user_point = (await session.execute(stmt)).scalar_one_or_none()

        if user_point is None:
            user_point = SeasonUserPointOrm(season_id=game.season_id,
                                            user_id=r.user_id,
                                            point=0)
            session.add(user_point)

        user_point.point += r.raw_point

        # 记录SeasonUserPointChangeLog
        change_log = SeasonUserPointChangeLogOrm(user_id=r.user_id,
                                                 season_id=game.season_id,
                                                 change_type=SeasonUserPointChangeType.game,
                                                 change_point=r.raw_point,
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
        # 判断在此之后是否还变动过PT
        stmt = select(func.count(SeasonUserPointChangeLogOrm.id)).where(
            SeasonUserPointChangeLogOrm.season_id == change_log.season_id,
            SeasonUserPointChangeLogOrm.user_id == change_log.user_id,
            SeasonUserPointChangeLogOrm.id > change_log.id
        )
        cnt = (await session.execute(stmt)).scalar_one()

        if cnt != 0:
            raise BadRequestError("撤销结算失败，在该对局之后该用户PT发生了改变")

        user_point.point -= change_log.change_point
        await session.delete(change_log)

        # 若用户只有这一次PT变动，则删除PT记录
        stmt = select(func.count(SeasonUserPointChangeLogOrm.id)).where(
            SeasonUserPointChangeLogOrm.season_id == user_point.season_id,
            SeasonUserPointChangeLogOrm.user_id == user_point.user_id,
        )
        cnt = (await session.execute(stmt)).scalar_one()

        if cnt == 0:
            await session.delete(user_point)

    await session.commit()
