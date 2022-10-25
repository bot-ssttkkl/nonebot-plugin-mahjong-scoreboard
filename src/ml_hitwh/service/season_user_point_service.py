from typing import Optional

from sqlalchemy.future import select
from sqlalchemy.sql.functions import count

from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.season import SeasonOrm, SeasonUserPointOrm
from ml_hitwh.model.orm.user import UserOrm


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
