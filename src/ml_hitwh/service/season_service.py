from datetime import datetime
from typing import Optional, List

from sqlalchemy import select

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import SeasonState, SeasonUserPointChangeType
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm, SeasonUserPointOrm, SeasonUserPointChangeLogOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import ensure_group_admin


async def _ensure_permission(season: SeasonOrm, operator: UserOrm):
    session = data_source.session()

    group = await session.get(GroupOrm, season.group_id)
    await ensure_group_admin(operator, group)


async def new_season(season: SeasonOrm) -> SeasonOrm:
    session = data_source.session()
    session.add(season)
    await session.commit()
    return season


async def get_season_by_code(season_code: str, group: GroupOrm) -> Optional[SeasonOrm]:
    session = data_source.session()
    stmt = select(SeasonOrm).where(
        SeasonOrm.group_id == group.id,
        SeasonOrm.code == season_code,
        SeasonOrm.accessible
    ).limit(1)
    season = (await session.execute(stmt)).scalar_one_or_none()
    return season


async def get_season_by_id(season_id: int) -> Optional[SeasonOrm]:
    session = data_source.session()
    stmt = select(SeasonOrm).where(
        SeasonOrm.id == season_id,
        SeasonOrm.accessible
    ).limit(1)
    season = (await session.execute(stmt)).scalar_one_or_none()
    return season


async def get_all_seasons(group: GroupOrm) -> List[SeasonOrm]:
    session = data_source.session()
    stmt = select(SeasonOrm).where(
        SeasonOrm.group == group,
        SeasonOrm.accessible
    )
    result = await session.execute(stmt)
    return [row[0] for row in result]


async def start_season(season: SeasonOrm, operator: UserOrm):
    await _ensure_permission(season, operator)

    session = data_source.session()

    group: GroupOrm = await session.get(GroupOrm, season.group_id)
    if season.state != SeasonState.initial:
        raise BadRequestError("该赛季已经开启或已经结束")
    if group.running_season_id:
        raise BadRequestError("当前已经有开启的赛季")

    season.state = SeasonState.running
    season.start_time = datetime.utcnow()
    group.running_season_id = season.id

    season.update_time = datetime.utcnow()
    await session.commit()


async def finish_season(season: SeasonOrm, operator: UserOrm):
    await _ensure_permission(season, operator)

    session = data_source.session()
    group: GroupOrm = await session.get(GroupOrm, season.group_id)

    if season.state != SeasonState.running:
        raise BadRequestError("该赛季尚未开启或已经结束")

    season.state = SeasonState.finished
    season.finish_time = datetime.utcnow()
    group.running_season_id = None

    season.update_time = datetime.utcnow()
    await session.commit()


async def remove_season(season: SeasonOrm, operator: UserOrm):
    await _ensure_permission(season, operator)

    session = data_source.session()

    if season.state != SeasonState.initial:
        raise BadRequestError("该赛季已经开启或已经结束")

    season.accessible = False
    season.delete_time = datetime.utcnow()
    season.update_time = datetime.utcnow()
    await session.commit()
