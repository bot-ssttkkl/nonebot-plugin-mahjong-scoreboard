from datetime import datetime

import tzlocal

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.game import Game, GameRecord, GameState

__all__ = ("new_game", "record")


async def next_game_id(now: datetime):
    today_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await Game.find(Game.create_time >= today_begin).count()
    return today_begin.year % 100 * 100_0000 + today_begin.month * 1_0000 + today_begin.day * 100 + today_count + 1


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