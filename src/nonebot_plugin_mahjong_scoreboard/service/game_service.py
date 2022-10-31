from datetime import datetime, timedelta
from math import ceil
from typing import List, Optional, Tuple, overload

import tzlocal
from nonebot import logger, require
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.enums import GameState, PlayerAndWind, Wind, SeasonState
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm, GameRecordOrm, GameProgressOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import is_group_admin
from nonebot_plugin_mahjong_scoreboard.service.season_user_point_service import revert_season_user_point_by_game, \
    change_season_user_point_by_game
from nonebot_plugin_mahjong_scoreboard.utils.date import encode_date
from nonebot_plugin_mahjong_scoreboard.utils.integer import count_digit

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="*/2", id="delete_all_uncompleted_game")
async def _delete_all_uncompleted_game():
    async with AsyncSession(data_source.engine) as session:
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        stmt = (update(GameOrm)
                .where(GameOrm.state != GameState.completed,
                       GameOrm.create_time > one_day_ago,
                       GameOrm.progress == None,
                       GameOrm.accessible)
                .values(accesible=False, delete_time=now, update_time=now)
                .execution_options(synchronize_session=False))
        result = await session.execute(stmt)
        await session.commit()
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
            if season.config["south_game_enabled"]:
                player_and_wind = PlayerAndWind.four_men_south
            else:
                player_and_wind = PlayerAndWind.four_men_east
        else:
            player_and_wind = PlayerAndWind.four_men_south
    else:
        if group.running_season_id is not None:
            season = await session.get(SeasonOrm, group.running_season_id)
            if player_and_wind == PlayerAndWind.four_men_south and not season.config["south_game_enabled"] \
                    or player_and_wind == PlayerAndWind.four_men_east and not season.config["east_game_enabled"]:
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


def _build_game_query(stmt: Select,
                      *, offset: Optional[int] = None,
                      limit: Optional[int] = None,
                      uncompleted_only: bool = False,
                      reverse_order: bool = False,
                      time_span: Optional[Tuple[datetime, datetime]] = None):
    if uncompleted_only:
        stmt.append_whereclause(GameOrm.state != GameState.completed)

    if reverse_order:
        stmt = stmt.order_by(GameOrm.id.desc())
    else:
        stmt = stmt.order_by(GameOrm.id)

    if time_span:
        stmt.append_whereclause(GameOrm.create_time >= time_span[0])
        stmt.append_whereclause(GameOrm.create_time < time_span[1])

    stmt.append_whereclause(GameOrm.accessible)

    stmt = (stmt.offset(offset).limit(limit)
            .options(selectinload(GameOrm.records)))

    return stmt


async def get_game_by_code(game_code: int, group: GroupOrm) -> Optional[GameOrm]:
    session = data_source.session()

    stmt = select(GameOrm).where(
        GameOrm.group == group, GameOrm.code == game_code
    )
    stmt = _build_game_query(stmt, limit=1)
    game = (await session.execute(stmt)).scalar_one_or_none()
    return game


@overload
async def get_user_games(group: GroupOrm, user: UserOrm,
                         *, uncompleted_only: bool = False,
                         offset: Optional[int] = None,
                         limit: Optional[int] = None,
                         reverse_order: bool = False,
                         time_span: Optional[Tuple[datetime, datetime]] = None) -> List[GameOrm]:
    ...


async def get_user_games(group: GroupOrm, user: UserOrm, **kwargs) -> List[GameOrm]:
    session = data_source.session()

    stmt = (select(GameOrm).join(GameRecordOrm)
            .where(GameOrm.group == group, GameRecordOrm.user == user))
    stmt = _build_game_query(stmt, **kwargs)

    result = await session.execute(stmt)
    return [row[0] for row in result]


@overload
async def get_group_games(group: GroupOrm,
                          *, uncompleted_only: bool = False,
                          offset: Optional[int] = None,
                          limit: Optional[int] = None,
                          reverse_order: bool = False,
                          time_span: Optional[Tuple[datetime, datetime]] = None) -> List[GameOrm]:
    ...


async def get_group_games(group: GroupOrm, **kwargs) -> List[GameOrm]:
    session = data_source.session()

    stmt = select(GameOrm).where(GameOrm.group == group)
    stmt = _build_game_query(stmt, **kwargs)

    result = await session.execute(stmt)
    return [row[0] for row in result]


@overload
async def get_season_games(season: SeasonOrm,
                           *, uncompleted_only: bool = False,
                           offset: Optional[int] = None,
                           limit: Optional[int] = None,
                           reverse_order: bool = False,
                           time_span: Optional[Tuple[datetime, datetime]] = None) -> List[GameOrm]:
    ...


async def get_season_games(season: SeasonOrm, **kwargs) -> List[GameOrm]:
    session = data_source.session()

    stmt = select(GameOrm).where(GameOrm.season == season)
    stmt = _build_game_query(stmt, **kwargs)

    result = await session.execute(stmt)
    return [row[0] for row in result]


async def _ensure_updatable(game: GameOrm):
    session = data_source.session()
    if game.season_id is not None:
        season = await session.get(SeasonOrm, game.season_id)
        if season.state != SeasonState.running:
            raise BadRequestError("赛季已经结束，无法再修改对局")


async def _ensure_permission(game: GameOrm, group: GroupOrm, operator: UserOrm):
    if game.state == GameState.completed:
        completed_before_24h = datetime.now() - game.complete_time >= timedelta(days=1)

        if not completed_before_24h or await is_group_admin(operator, group):
            return

        raise BadRequestError("对局已完成超过24小时，需要管理员权限才能操作")


async def record_game(game_code: int,
                      group: GroupOrm,
                      user: UserOrm,
                      score: int,
                      wind: Optional[Wind],
                      operator: UserOrm) -> GameOrm:
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)
    await _ensure_permission(game, group, operator)

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break
    else:
        if len(game.records) == 4:
            raise BadRequestError("这场对局已经存在4人记录")

        record = GameRecordOrm(game_id=game.id, user_id=user.id)
        session.add(record)
        game.records.append(record)

    if game.state == GameState.completed and game.season_id:
        await revert_season_user_point_by_game(game)

    game.state = GameState.uncompleted
    record.score = score
    record.wind = wind

    if len(game.records) == 4:
        await _handle_full_recorded_game(game)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def _handle_full_recorded_game(game: GameOrm):
    session = data_source.session()

    progress = await session.get(GameProgressOrm, game.id)
    if progress is not None:
        return

    # 总分校验
    sum_score = sum(map(lambda r: r.score, game.records))
    if sum_score != 25000 * 4:
        game.state = GameState.invalid_total_point
        return

    game.state = GameState.completed
    game.complete_time = datetime.now()

    # 计算pt
    if not game.season_id:
        return

    season = await session.get(SeasonOrm, game.season_id)
    if game.player_and_wind == PlayerAndWind.four_men_east:
        horse_point = season.config["east_game_horse_point"]
        origin_point = season.config["east_game_origin_point"]
    elif game.player_and_wind == PlayerAndWind.four_men_south:
        horse_point = season.config["south_game_horse_point"]
        origin_point = season.config["south_game_origin_point"]
    else:
        raise ValueError("invalid players and wind")

    # 降序排序（带上原索引）
    indexed_record: List[Tuple[GameRecordOrm, int]] = [(r, i) for i, r in enumerate(game.records)]
    indexed_record.sort(key=lambda tup: tup[0].score, reverse=True)

    # 处理同分
    # 四人幸终
    if indexed_record[0][0].score == indexed_record[1][0].score == \
            indexed_record[2][0].score == indexed_record[3][0].score:
        _divide_horse_point(indexed_record, horse_point, 0, 3)
    # 一二三位同分
    elif indexed_record[0][0].score == indexed_record[1][0].score == indexed_record[2][0].score:
        _divide_horse_point(indexed_record, horse_point, 0, 2)
    # 二三四位同分
    elif indexed_record[1][0].score == indexed_record[2][0].score == indexed_record[3][0].score:
        _divide_horse_point(indexed_record, horse_point, 1, 3)
    # 一二位同分
    elif indexed_record[0][0].score == indexed_record[1][0].score:
        _divide_horse_point(indexed_record, horse_point, 0, 1)

        # 且三四位同分
        if indexed_record[2][0].score == indexed_record[3][0].score:
            _divide_horse_point(indexed_record, horse_point, 2, 3)
    # 二三位同分
    elif indexed_record[1][0].score == indexed_record[2][0].score:
        _divide_horse_point(indexed_record, horse_point, 1, 2)
    # 三四位同分
    elif indexed_record[2][0].score == indexed_record[3][0].score:
        _divide_horse_point(indexed_record, horse_point, 2, 3)

    for i, (r, j) in enumerate(indexed_record):
        # （点数-返点+马点）/1000，切上
        r.point = horse_point[i] + ceil((r.score - origin_point) / 1000)

    await change_season_user_point_by_game(game)


def _divide_horse_point(indexed_record: List[Tuple[GameRecordOrm, int]], horse_point: List[int], start: int, end: int):
    sum_horse_point = sum(horse_point[start:end + 1])
    divided_horse_point = sum_horse_point // (end - start + 1)

    for i in range(start, end + 1):
        horse_point[i] = divided_horse_point

    if divided_horse_point * (end - start + 1) != sum_horse_point:
        min_index = start
        for i in range(start + 1, end + 1):
            if indexed_record[i][1] < indexed_record[min_index][1]:
                min_index = i
        horse_point[min_index] += sum_horse_point - divided_horse_point * (end - start + 1)


async def revert_record(game_code: int,
                        group: GroupOrm,
                        user: UserOrm,
                        operator: UserOrm) -> GameOrm:
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)
    await _ensure_permission(game, group, operator)

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break
    else:
        raise BadRequestError("你还没有记录过这场对局")

    if game.state == GameState.completed and game.season_id:
        await revert_season_user_point_by_game(game)

    game.state = GameState.uncompleted
    game.records.remove(record)
    await session.delete(record)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def delete_game(game_code: int,
                      group: GroupOrm,
                      operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)

    if not await is_group_admin(operator, group):
        raise BadRequestError("需要管理员权限进行该操作")

    if game.state == GameState.completed and game.season_id:
        await revert_season_user_point_by_game(game)

    game.accessible = False
    game.delete_time = datetime.now()
    game.update_time = datetime.now()
    await session.commit()


async def delete_uncompleted_season_games(season: SeasonOrm):
    session = data_source.session()
    now = datetime.utcnow()
    stmt = (update(GameOrm)
            .where(GameOrm.season == season, GameOrm.state != GameState.completed, GameOrm.accessible)
            .values(accesible=False, delete_time=now, update_time=now)
            .execution_options(synchronize_session=False))
    await session.execute(stmt)
    await session.commit()


async def make_game_progress(game_code: int, round: int, honba: int,
                             group: GroupOrm, operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)
    await _ensure_permission(game, group, operator)

    if game.state == GameState.completed and game.season_id:
        await revert_season_user_point_by_game(game)

    game.state = GameState.uncompleted

    progress = await session.get(GameProgressOrm, game.id)
    if progress is None:
        progress = GameProgressOrm(game_id=game.id)
        session.add(progress)

    progress.round = round
    progress.honba = honba

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def remove_game_progress(game_code: int, group: GroupOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)

    progress = await session.get(GameProgressOrm, game.id)
    if progress is not None:
        # 不能用session.delete，否则之后session.get还能获取到
        stmt = delete(GameProgressOrm).where(GameProgressOrm.game_id == game.id)
        await session.execute(stmt)

        if len(game.records) == 4:
            await _handle_full_recorded_game(game)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def set_record_point(game_code: int, group: GroupOrm, user: UserOrm, point: int, operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)
    await _ensure_permission(game, group, operator)

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break
    else:
        raise BadRequestError("你还没有记录过这场对局")

    if game.state != GameState.completed:
        raise BadRequestError("这场对局未处于完成状态")

    if game.season_id is None:
        raise BadRequestError("这场对局不属于赛季")

    await revert_season_user_point_by_game(game)
    record.point = point
    await change_season_user_point_by_game(game)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def set_game_comment(game_code: int, group: GroupOrm, comment: str, operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_updatable(game)
    await _ensure_permission(game, group, operator)

    game.comment = comment

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


__all__ = ("get_game_by_code", "get_group_games", "get_season_games", "get_user_games",
           "new_game", "delete_game", "record_game", "revert_record", "set_record_point",
           "make_game_progress", "remove_game_progress")
