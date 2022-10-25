from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ml_hitwh.model.enums import GameState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.model.orm.user import UserOrm


async def get_game_by_code(game_code: int, group: GroupOrm, *options) -> Optional[GameOrm]:
    session = data_source.session()

    stmt = select(GameOrm).where(
        GameOrm.group == group, GameOrm.code == game_code, GameOrm.accessible
    ).limit(1).options(selectinload(GameOrm.records), *options)
    game: GameOrm = (await session.execute(stmt)).scalar_one_or_none()
    return game


async def get_user_games(group: GroupOrm, user: UserOrm,
                         uncompleted_only: bool = False,
                         *, offset: Optional[int] = None,
                         limit: Optional[int] = None,
                         reverse_order: bool = False) -> List[GameOrm]:
    session = data_source.session()

    where = [GameOrm.group == group, GameRecordOrm.user == user]
    if uncompleted_only:
        where.append(GameOrm.state != GameState.completed)

    stmt = select(GameOrm).join(GameRecordOrm).where(*where).offset(offset).limit(limit)

    if reverse_order:
        stmt = stmt.order_by(GameOrm.id.desc())

    result = await session.execute(stmt)
    return [row[0] for row in result]


async def get_group_games(group: GroupOrm,
                          uncompleted_only: bool = False,
                          *, offset: Optional[int] = None,
                          limit: Optional[int] = None,
                          reverse_order: bool = False) -> List[GameOrm]:
    session = data_source.session()

    where = [GameOrm.group == group]
    if uncompleted_only:
        where.append(GameOrm.state != GameState.completed)

    stmt = select(GameOrm).where(*where).offset(offset).limit(limit)

    if reverse_order:
        stmt = stmt.order_by(GameOrm.id.desc())

    result = await session.execute(stmt)
    return [row[0] for row in result]


async def get_season_games(season: SeasonOrm,
                           uncompleted_only: bool = False,
                           *, offset: Optional[int] = None,
                           limit: Optional[int] = None,
                           reverse_order: bool = False) -> List[GameOrm]:
    session = data_source.session()

    where = [GameOrm.season == season]
    if uncompleted_only:
        where.append(GameOrm.state != GameState.completed)

    stmt = select(GameOrm).where(*where).offset(offset).limit(limit)

    if reverse_order:
        stmt = stmt.order_by(GameOrm.id.desc())

    result = await session.execute(stmt)
    return [row[0] for row in result]
