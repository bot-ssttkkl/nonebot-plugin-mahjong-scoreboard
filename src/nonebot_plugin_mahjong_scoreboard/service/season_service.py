from datetime import datetime
from typing import Optional, List

from .game_service import delete_uncompleted_season_games
from .group_service import is_group_admin
from .mapper import map_season
from ..errors import ResultError, BadRequestError
from ..model import Season, SeasonConfig, SeasonState
from ..repository import data_source
from ..repository.data_model import GroupOrm, SeasonOrm
from ..repository.season import SeasonRepository


async def _ensure_permission(season: SeasonOrm, operator_user_id: int):
    if not await is_group_admin(operator_user_id, season.group_id):
        raise BadRequestError("没有权限")


async def new_season(group_id: int, code: str, name: str, config: SeasonConfig) -> Season:
    session = data_source.session()

    season = SeasonOrm(
        code=code,
        name=name,
        config=config,
        group_id=group_id
    )
    session.add(season)
    await session.commit()
    await session.refresh(season)
    return await map_season(season, session)


async def get_season_by_code(season_code: str, group_id: int) -> Optional[Season]:
    session = data_source.session()
    repo = SeasonRepository(session)
    season = await repo.get_by_code(season_code, group_id)
    return await map_season(season, session)


async def get_season_by_id(season_id: int) -> Optional[Season]:
    session = data_source.session()
    repo = SeasonRepository(session)
    season = await repo.get_by_pk(season_id)
    return await map_season(season, session)


async def get_group_seasons(group_id: int) -> List[Season]:
    session = data_source.session()
    repo = SeasonRepository(session)
    seasons = await repo.get_group_seasons(group_id)
    return [await map_season(s, session) for s in seasons]


async def get_group_running_season(group_id: int) -> Optional[Season]:
    session = data_source.session()
    group = await session.get(GroupOrm, group_id)
    repo = SeasonRepository(session)
    if group.running_season_id:
        season = await repo.get_by_pk(group.running_season_id)
        return await map_season(season, session)
    else:
        return None


async def start_season(season_id: int, operator_user_id: int):
    session = data_source.session()

    repo = SeasonRepository(session)

    season = await repo.get_by_pk(season_id)

    await _ensure_permission(season, operator_user_id)

    group: GroupOrm = await session.get(GroupOrm, season.group_id)
    if season.state != SeasonState.initial:
        raise ResultError("该赛季已经开启或已经结束")
    if group.running_season_id:
        raise ResultError("当前已经有开启的赛季")

    season.state = SeasonState.running
    season.start_time = datetime.utcnow()
    group.running_season_id = season.id

    season.update_time = datetime.utcnow()
    await session.commit()


async def finish_season(season_id: int, operator_user_id: int):
    session = data_source.session()

    repo = SeasonRepository(session)

    season = await repo.get_by_pk(season_id)

    await _ensure_permission(season, operator_user_id)

    if season.state != SeasonState.running:
        raise ResultError("该赛季尚未开启或已经结束")

    await delete_uncompleted_season_games(season.id)

    season.state = SeasonState.finished
    season.finish_time = datetime.utcnow()

    group = await session.get(GroupOrm, season.group_id)
    group.running_season_id = None

    season.update_time = datetime.utcnow()
    await session.commit()


async def remove_season(season_id: int, operator_user_id: int):
    session = data_source.session()

    repo = SeasonRepository(session)

    season = await repo.get_by_pk(season_id)

    await _ensure_permission(season, operator_user_id)

    if season.state != SeasonState.initial:
        raise ResultError("该赛季已经开启或已经结束")

    season.accessible = False
    season.delete_time = datetime.utcnow()
    season.update_time = datetime.utcnow()
    await session.commit()
