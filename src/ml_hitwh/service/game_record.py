from asyncio import Lock
from datetime import datetime
from math import log, ceil

import tzlocal

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.game import Game, GameRecord, GameState

__all__ = ("new_game", "record")

game_counter = 0
game_counter_date = None
game_counter_sync_mutex = Lock()


async def next_game_id(now: datetime):
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

    return (today_begin.year % 100 * 10000 + today_begin.month * 100 + today_begin.day) * num_digit + num


async def new_game(create_user_id: int, group_id: int) -> Game:
    now = datetime.now(tzlocal.get_localzone())
    game_id = await next_game_id(now)
    game = Game(game_id=game_id,
                group_id=group_id,
                create_user_id=create_user_id,
                create_time=now)

    await game.insert()
    return game


async def record(game_id: int, user_id: int, point: int) -> Game:
    game = await Game.find_one(Game.game_id == game_id)
    if game is None:
        raise BadRequestError("未找到对局")
    if game.state != GameState.uncompleted:
        raise BadRequestError("这场对局不处于未完成状态")

    for r in game.record:
        if r.user_id == user_id:
            raise BadRequestError("你已经记录过这场对局了，可以对此消息回复“撤销结算”指令撤销你的分数后重新记录")

    game.record.append(GameRecord(user_id=user_id, point=point))

    if len(game.record) == 4:
        if sum(map(lambda r: r.point, game.record)) != 100000:
            game.state = GameState.invalid_total_point
        else:
            game.state = GameState.completed

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

    game.state = GameState.uncompleted
    await game.save()
    return game


async def delete_game(game_id: int) -> bool:
    result = await Game.find_one(Game.game_id == game_id).delete_one()
    return result.deleted_count == 1
