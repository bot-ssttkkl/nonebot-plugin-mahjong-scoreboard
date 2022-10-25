from datetime import datetime, timedelta
from typing import List, Optional

import tzlocal
from nonebot import logger, require
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import GameState, PlayerAndWind
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.utils import count_digit, encode_date

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="*/2", id="delete_all_uncompleted_game")
async def _delete_all_uncompleted_game():
    session = data_source.session()

    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    stmt = delete(GameOrm).where(GameOrm.state != GameState.completed,
                                 GameOrm.create_time > one_day_ago,
                                 GameOrm.progress_id == None)
    result = await session.execute(stmt)
    logger.success(f"deleted {result.rowcount} outdated uncompleted game(s)")


async def new_game(promoter: UserOrm,
                   group: GroupOrm,
                   player_and_wind: Optional[PlayerAndWind]) -> GameOrm:
    session = data_source.session()

    now = datetime.now(tzlocal.get_localzone())
    game_code_base = encode_date(now)
    if game_code_base != group.prev_game_code_base:
        group.prev_game_code_base = game_code_base
        group.prev_game_code_identifier = 0

    group.prev_game_code_identifier += 1

    digit = max(2, count_digit(group.prev_game_code_identifier))
    game_code = group.prev_game_code_base * (10 ** digit) + group.prev_game_code_identifier

    # 未指定player_and_wind时，若赛季启用了半庄则默认为半庄，否则为东风
    if player_and_wind is None:
        if group.running_season_id is not None:
            season = await session.get(SeasonOrm, group.running_season_id)
            if season.south_game_enabled:
                player_and_wind = PlayerAndWind.four_men_south
            else:
                player_and_wind = PlayerAndWind.four_men_east
        else:
            player_and_wind = PlayerAndWind.four_men_south
    else:
        if group.running_season_id is not None:
            season = await session.get(SeasonOrm, group.running_season_id)
            if player_and_wind == PlayerAndWind.four_men_south and not season.south_game_enabled \
                    or player_and_wind == PlayerAndWind.four_men_east and not season.east_game_enabled:
                raise BadRequestError("当前赛季未开放此类型对局")

    game = GameOrm(code=game_code,
                   group_id=group.id,
                   promoter_user_id=promoter.id,
                   player_and_wind=player_and_wind,
                   season_id=group.running_season_id,
                   records=[])

    session.add(game)
    await session.commit()
    return game


async def get_game_by_code(game_code: int, group: GroupOrm) -> Optional[GameOrm]:
    session = data_source.session()

    stmt = select(GameOrm).where(
        GameOrm.group == group, GameOrm.code == game_code, GameOrm.accessible
    ).limit(1).options(selectinload(GameOrm.records))
    game: Optional[GameOrm] = (await session.execute(stmt)).scalar_one_or_none()
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

    stmt = (select(GameOrm).join(GameRecordOrm).where(*where)
            .offset(offset).limit(limit)
            .options(selectinload(GameOrm.records)))

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

    stmt = (select(GameOrm).where(*where)
            .offset(offset).limit(limit)
            .options(selectinload(GameOrm.records)))

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

    stmt = (select(GameOrm).where(*where)
            .offset(offset).limit(limit)
            .options(selectinload(GameOrm.records)))

    if reverse_order:
        stmt = stmt.order_by(GameOrm.id.desc())

    result = await session.execute(stmt)
    return [row[0] for row in result]
