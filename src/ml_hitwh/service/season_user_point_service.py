from typing import Optional, List

from sqlalchemy.future import select
from sqlalchemy.sql.functions import count

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import SeasonUserPointChangeType
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm, SeasonUserPointOrm, SeasonUserPointChangeLogOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import is_group_admin


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


async def set_season_user_point(season: SeasonOrm, user: UserOrm, point: int, operator: UserOrm) -> SeasonUserPointOrm:
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

    await session.commit()
    return sup
