from typing import Optional

from sqlalchemy import select

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import SeasonState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm


async def new_season(season: SeasonOrm) -> SeasonOrm:
    session = data_source.session()
    session.add(season)
    await session.commit()
    return season


async def get_season_by_code(season_code: str, group: GroupOrm) -> Optional[SeasonOrm]:
    session = data_source.session()
    stmt = select(SeasonOrm).where(
        SeasonOrm.group_id == group.id,
        SeasonOrm.code == season_code
    ).limit(1)
    season = (await session.execute(stmt)).scalar_one_or_none()
    return season


async def get_season_by_id(season_id: int) -> Optional[SeasonOrm]:
    session = data_source.session()
    stmt = select(SeasonOrm).where(
        SeasonOrm.id == season_id
    ).limit(1)
    season = (await session.execute(stmt)).scalar_one_or_none()
    return season


async def start_season(season: SeasonOrm):
    session = data_source.session()
    group: GroupOrm = await session.get(GroupOrm, season.group_id)
    if group.running_season_id:
        raise BadRequestError("当前已经有开启的赛季")

    season.state = SeasonState.running
    group.running_season_id = season.id

    await session.commit()
