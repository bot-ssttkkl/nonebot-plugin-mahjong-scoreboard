from datetime import datetime
from math import ceil
from typing import List, Tuple

import tzlocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import PlayerAndWind, GameState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.service.user_service import get_user_by_binding_qq
from ml_hitwh.utils import encode_date, count_digit

__all__ = ("new_game", "record_game")


async def new_game(promoter_user_binding_qq: int,
                   group_binding_qq: int,
                   player_and_wind: PlayerAndWind) -> GameOrm:
    session = data_source.session()
    promoter = await get_user_by_binding_qq(promoter_user_binding_qq)
    group = await get_group_by_binding_qq(group_binding_qq)

    now = datetime.now(tzlocal.get_localzone())
    game_code_base = encode_date(now)
    if game_code_base != group.prev_game_code_base:
        group.prev_game_code_base = game_code_base
        group.prev_game_code_identifier = 0

    group.prev_game_code_identifier += 1

    digit = max(2, count_digit(group.prev_game_code_identifier))
    game_code = group.prev_game_code_base * (10 ** digit) + group.prev_game_code_identifier

    game = GameOrm(code=game_code,
                   group_id=group.id,
                   promoter_user_id=promoter.id,
                   player_and_wind=player_and_wind,
                   season_id=group.running_season_id)

    session.add(game)
    await session.commit()
    return game


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


async def _handle_full_recorded_game(game: GameOrm):
    session = data_source.session()

    # 总分校验
    sum_score = sum(map(lambda r: r.score, game.record))
    if sum_score != 25000 * 4:
        game.state = GameState.invalid_total_point
    else:
        game.state = GameState.completed

    # 计算pt
    stmt = select(GameOrm).execution_options(populate_existing=True).options(
        selectinload(GameOrm.season)
    )
    await session.execute(stmt)

    if game.season is None:
        return

    if game.player_and_wind == PlayerAndWind.four_men_east:
        horse_point = game.season.east_game_horse_point
    elif game.player_and_wind == PlayerAndWind.four_men_south:
        horse_point = game.season.south_game_horse_point
    else:
        raise ValueError("invalid players and wind")

    # 降序排序（带上原索引）
    indexed_record: List[Tuple[GameRecordOrm, int]] = [(r, i) for i, r in enumerate(game.record)]
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

    for i, r in enumerate(game.record):
        # 30000返，1000点=1pt
        # TODO: 动态配置
        r.point = horse_point[i] + ceil((r.score - 30000) / 1000)


async def record_game(game_code: int,
                      group_binding_qq: int,
                      user_binding_qq: int,
                      score: int) -> GameOrm:
    session = data_source.session()

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    stmt = select(GameOrm).where(
        GameOrm.group == group and GameOrm.game_code == game_code and GameOrm.accessible
    ).limit(1).options(
        selectinload(GameOrm.records)
    )
    game: GameOrm = (await session.execute(stmt)).scalar_one_or_none()

    if game is None:
        raise BadRequestError("未找到对局")
    if game.state != GameState.uncompleted:
        raise BadRequestError("这场对局不处于未完成状态")

    record = None

    for r in game.records:
        if r.user_id == user.id:
            record = r
            break

    if record is None:
        if len(game.records) == 4:
            raise BadRequestError("这场对局已经有4人记录")

        record = GameRecordOrm(game_id=game.id, user_id=user.id)
        game.records.append(record)

    record.score = score

    if len(game.records) == 4:
        await _handle_full_recorded_game(game)

    await session.commit()
    return game

# async def revert_record(game_id: int, user_id: int) -> GameOrm:
#     game = await GameOrm.find_one(GameOrm.game_id == game_id)
#     if game is None:
#         raise BadRequestError("未找到对局")
#
#     for r in game.record:
#         if r.user_id == user_id:
#             game.record.remove(r)
#             break
#     else:
#         raise BadRequestError("你还没有记录过这场对局")
#
#     if game.state == GameState.completed:
#         for r in game.record:
#             r.point = None
#
#     game.state = GameState.uncompleted
#
#     await game.save()
#     return game
#
#
# async def delete_game(game_id: int) -> bool:
#     result = await GameOrm.find_one(GameOrm.game_id == game_id).delete_one()
#     return result.deleted_count == 1
