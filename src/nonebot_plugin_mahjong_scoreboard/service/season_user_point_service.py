from typing import Optional, List

from .group_service import is_group_admin
from .mapper import map_season_user_point, map_season_user_point_change_log
from ..errors import BadRequestError
from ..model import SeasonUserPoint, SeasonUserPointChangeLog
from ..repository import data_source
from ..repository.season import SeasonRepository


async def get_season_user_point(season_id: int, user_id: int) -> Optional[SeasonUserPoint]:
    session = data_source.session()
    repo = SeasonRepository(session)
    sup = await repo.get_season_user_point(season_id, user_id)
    if sup is not None:
        sup = await map_season_user_point(sup, session)
        sup.rank = await repo.get_season_user_point_rank(season_id, sup.point)
        sup.total = await repo.count_season_user_point(season_id)
        return sup
    else:
        return None


async def get_season_user_points(season_id: int) -> List[SeasonUserPoint]:
    session = data_source.session()
    repo = SeasonRepository(session)
    sups = await repo.get_season_user_points(season_id)
    sups = [await map_season_user_point(x, session) for x in sups]

    for i, x in enumerate(sups):
        x.rank = i + 1
        x.total = len(sups)

    return sups


async def get_season_user_point_change_logs(season_id: Optional[int] = None,
                                            user_id: Optional[int] = None) -> List[SeasonUserPointChangeLog]:
    session = data_source.session()
    repo = SeasonRepository(session)
    logs = await repo.get_season_user_point_change_logs(season_id, user_id)
    logs = [await map_season_user_point_change_log(x, session) for x in logs]
    return logs


async def reset_season_user_point(season_id: int,
                                  group_id: int,
                                  user_id: int,
                                  operator_user_id: int):
    if not await is_group_admin(operator_user_id, group_id):
        raise BadRequestError("没有权限")

    session = data_source.session()
    repo = SeasonRepository(session)

    await repo.reset_season_user_point(season_id, user_id)


async def change_season_user_point_manually(season_id: int,
                                            group_id: int,
                                            user_id: int,
                                            point: float,
                                            operator_user_id: int) -> SeasonUserPoint:
    if not await is_group_admin(operator_user_id, group_id):
        raise BadRequestError("没有权限")

    session = data_source.session()
    repo = SeasonRepository(session)

    sup = await repo.change_season_user_point_manually(season_id, user_id, point)
    return await map_season_user_point(sup, session)
