from datetime import datetime, timedelta
from math import ceil
from typing import List, Optional, Tuple, overload

import tzlocal
from nonebot import logger, require
from sqlalchemy import and_
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import GameState, PlayerAndWind
from ml_hitwh.model.enums import SeasonUserPointChangeType, Wind
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm
from ml_hitwh.model.orm.game import GameProgressOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.model.orm.season import SeasonUserPointOrm, SeasonUserPointChangeLogOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import is_group_admin
from ml_hitwh.utils.date import encode_date
from ml_hitwh.utils.integer import count_digit

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="*/2", id="delete_all_uncompleted_game")
async def _delete_all_uncompleted_game():
    session = data_source.session()

    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    stmt = delete(GameOrm).where(GameOrm.state != GameState.completed,
                                 GameOrm.create_time > one_day_ago,
                                 GameOrm.progress == None)
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


async def _ensure_permission(game: GameOrm, group: GroupOrm, operator: UserOrm):
    completed_before_24h = (game.state == GameState.completed and
                            datetime.now() - game.complete_time >= timedelta(days=1))

    if not completed_before_24h and game.promoter_user_id == operator.id:
        return
    if await is_group_admin(operator, group):
        return

    raise BadRequestError("没有权限")


async def record_game(game: GameOrm,
                      user: UserOrm,
                      score: int,
                      wind: Optional[Wind]) -> GameOrm:
    session = data_source.session()

    if game.state == GameState.completed:
        raise BadRequestError("这场对局已经处于完成状态")

    record = None

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break

    if record is None:
        if len(game.records) == 4:
            raise BadRequestError("这场对局已经存在4人记录")

        record = GameRecordOrm(game_id=game.id, user_id=user.id)
        session.add(record)
        game.records.append(record)

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
        horse_point = season.east_game_horse_point
    elif game.player_and_wind == PlayerAndWind.four_men_south:
        horse_point = season.south_game_horse_point
    else:
        raise ValueError("invalid players and wind")

    # 降序排序（带上原索引）
    indexed_record: List[Tuple[GameRecordOrm, int]] = [(r, i) for i, r in enumerate(game.records)]
    indexed_record.sort(key=lambda tup: tup[0].score, reverse=True)

    # 处理同分
    # TODO：动态配置
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
        # 30000返，1000点=1pt
        # TODO: 动态配置
        if r.point is None:
            # 已经设置过PT的直接忽略
            r.point = horse_point[i] + ceil((r.score - 30000) / 1000)

    await _make_season_user_point_change(game)


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


async def _make_season_user_point_change(game: GameOrm):
    session = data_source.session()

    for r in game.records:
        # 记录SeasonUserPoint
        stmt = select(SeasonUserPointOrm).where(
            SeasonUserPointOrm.season_id == game.season_id,
            SeasonUserPointOrm.user_id == r.user_id
        ).limit(1)
        user_point = (await session.execute(stmt)).scalar_one_or_none()

        if user_point is None:
            user_point = SeasonUserPointOrm(season_id=game.season_id, user_id=r.user_id, point=0)
            session.add(user_point)

        user_point.point += r.point

        # 记录SeasonUserPointChangeLog
        change_log = SeasonUserPointChangeLogOrm(user_id=r.user_id,
                                                 season_id=game.season_id,
                                                 change_type=SeasonUserPointChangeType.game,
                                                 change_point=r.point,
                                                 related_game_id=game.id)
        session.add(change_log)

    # 这里不需要commit


async def revert_record(game_code: int,
                        group: GroupOrm,
                        user: UserOrm,
                        operator: UserOrm) -> GameOrm:
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break
    else:
        raise BadRequestError("你还没有记录过这场对局")

    if game.state == GameState.completed:
        await _ensure_permission(game, group, operator)

        if game.season_id:
            await _revert_season_user_point_change(game)

    game.state = GameState.uncompleted
    game.records.remove(record)
    await session.delete(record)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


async def _revert_season_user_point_change(game: GameOrm):
    session = data_source.session()

    stmt = select(SeasonUserPointChangeLogOrm, SeasonUserPointOrm).join_from(
        SeasonUserPointChangeLogOrm, SeasonUserPointOrm, and_(
            SeasonUserPointChangeLogOrm.user_id == SeasonUserPointOrm.user_id,
            SeasonUserPointChangeLogOrm.season_id == SeasonUserPointOrm.season_id,
        )
    ).where(
        SeasonUserPointChangeLogOrm.related_game_id == game.id
    )

    for change_log, user_point in await session.execute(stmt):
        change_log: SeasonUserPointChangeLogOrm
        user_point: SeasonUserPointOrm

        user_point.point -= change_log.change_point

        await session.delete(change_log)

    # 这里不需要commit


async def delete_game(game_code: int,
                      group: GroupOrm,
                      operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    await _ensure_permission(game, group, operator)

    if game.state == GameState.completed and game.season_id:
        await _revert_season_user_point_change(game)

    game.accessible = False
    game.delete_time = datetime.now()

    await session.commit()


async def make_game_progress(game_code: int, round: int, honba: int,
                             group: GroupOrm, operator: UserOrm):
    session = data_source.session()

    game = await get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    if game.state == GameState.completed:
        await _ensure_permission(game, group, operator)

        if game.season_id:
            await _revert_season_user_point_change(game)

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

    progress = await session.get(GameProgressOrm, game.id)

    if progress is not None:
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

    await _ensure_permission(game, group, operator)

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break
    else:
        raise BadRequestError("你还没有记录过这场对局")

    if game.state == GameState.completed and game.season_id is not None:
        await _revert_season_user_point_change(game)

    record.point = point

    if len(game.records) == 4:
        await _handle_full_recorded_game(game)

    game.update_time = datetime.utcnow()
    await session.commit()
    return game


__all__ = ("get_game_by_code", "get_group_games", "get_season_games", "get_user_games",
           "new_game", "delete_game", "record_game", "revert_record", "set_record_point",
           "make_game_progress", "remove_game_progress")
