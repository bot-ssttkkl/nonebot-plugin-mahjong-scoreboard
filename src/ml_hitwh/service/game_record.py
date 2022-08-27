from asyncio import Lock
from datetime import datetime
from math import log, ceil
from typing import Tuple, List

import tzlocal

from ml_hitwh.config import conf
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.game import Game, GameRecord, GameState, Wind

__all__ = ("new_game", "record", "revert_record", "delete_game")

from ml_hitwh.utils import encode_date

game_counter = 0
game_counter_date = None
game_counter_sync_mutex = Lock()


async def _next_game_id(now: datetime):
    global game_counter, game_counter_date

    # 判断是否需要从数据库同步计数
    if game_counter_date is None:
        async with game_counter_sync_mutex:
            if game_counter_date is None:
                today_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
                game_counter = await Game.find(Game.create_time >= today_begin).count()
                game_counter_date = now.date()

    if game_counter_date != now.date():
        game_counter_date = now.date()
        game_counter = 0

    game_counter += 1
    num = game_counter

    # 编号默认为2位，当天对局数超过100时再扩展
    if num < 100:
        num_digit = 2
    else:
        num_digit = ceil(log(num, 10))

    return encode_date(now.date()) * (10 ** num_digit) + num


async def new_game(create_user_id: int, group_id: int, players: int, wind: Wind) -> Game:
    now = datetime.now(tzlocal.get_localzone())
    game_id = await _next_game_id(now)
    game = Game(game_id=game_id,
                group_id=group_id,
                players=players,
                wind=wind,
                create_user_id=create_user_id,
                create_time=now)

    await game.insert()
    return game


def _divide_horse_point(indexed_record: List[Tuple[GameRecord, int]], horse_point: List[int], start: int, end: int):
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


def _handle_full_recorded_four_men_game(game: Game):
    sum_score = sum(map(lambda r: r.score, game.record))
    if sum_score != 25000 * 4:
        game.state = GameState.invalid_total_point
    else:
        game.state = GameState.completed

    # 计算pt
    indexed_record: List[Tuple[GameRecord, int]] = [(r, i) for i, r in enumerate(game.record)]
    indexed_record.sort(key=lambda tup: tup[0].score, reverse=True)

    if game.wind == Wind.SOUTH:
        horse_point = conf.ml_horse_point_four_men_south.copy()
    elif game.wind == Wind.EAST:
        horse_point = conf.ml_horse_point_four_men_east.copy()
    else:
        raise ValueError("invalid players and wind")

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

    for i, r in enumerate(game.record):
        # 30000返，1000点=1pt
        r.point = horse_point[i] + ceil((r.score - 30000) / 1000)


def _handle_full_recorded_three_men_game(game: Game):
    sum_score = sum(map(lambda r: r.score, game.record))
    if sum_score != 35000 * 3:
        game.state = GameState.invalid_total_point
    else:
        game.state = GameState.completed

    # 计算pt
    indexed_record: List[Tuple[GameRecord, int]] = [(r, i) for i, r in enumerate(game.record)]
    indexed_record.sort(key=lambda tup: tup[0].score, reverse=True)

    if game.wind == Wind.SOUTH:
        horse_point = conf.ml_horse_point_three_men_south
    elif game.wind == Wind.EAST:
        horse_point = conf.ml_horse_point_three_men_east
    else:
        raise ValueError("invalid players and wind")

    # 处理同分
    # 三人幸终
    if indexed_record[0][0].score == indexed_record[1][0].score == indexed_record[2][0].score:
        _divide_horse_point(indexed_record, horse_point, 0, 2)
    # 一二位同分
    elif indexed_record[0][0].score == indexed_record[1][0].score:
        _divide_horse_point(indexed_record, horse_point, 0, 1)
    # 二三位同分
    elif indexed_record[1][0].score == indexed_record[2][0].score:
        _divide_horse_point(indexed_record, horse_point, 1, 2)

    for i, r in enumerate(game.record):
        # 40000返，1000点=1pt（待确认）
        r.point = horse_point[i] + ceil((r.score - 40000) / 1000)


async def record(game_id: int, user_id: int, score: int) -> Game:
    game = await Game.find_one(Game.game_id == game_id)
    if game is None:
        raise BadRequestError("未找到对局")
    if game.state != GameState.uncompleted:
        raise BadRequestError("这场对局不处于未完成状态")

    for r in game.record:
        if r.user_id == user_id:
            raise BadRequestError("你已经记录过这场对局了，可以对此消息回复“撤销结算”指令撤销你的分数后重新记录")

    game.record.append(GameRecord(user_id=user_id, score=score))

    if len(game.record) == game.players:
        if game.players == 4:
            _handle_full_recorded_four_men_game(game)
        else:
            _handle_full_recorded_three_men_game(game)

    await game.save()
    return game


async def revert_record(game_id: int, user_id: int) -> Game:
    game = await Game.find_one(Game.game_id == game_id)
    if game is None:
        raise BadRequestError("未找到对局")

    for r in game.record:
        if r.user_id == user_id:
            game.record.remove(r)
            break
    else:
        raise BadRequestError("你还没有记录过这场对局")

    if game.state == GameState.completed:
        for r in game.record:
            r.point = None

    game.state = GameState.uncompleted

    await game.save()
    return game


async def delete_game(game_id: int) -> bool:
    result = await Game.find_one(Game.game_id == game_id).delete_one()
    return result.deleted_count == 1

