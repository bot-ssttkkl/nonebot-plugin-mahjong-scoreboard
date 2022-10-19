from io import StringIO
from typing import TextIO, Iterable, Optional, Union

from nonebot import Bot
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ml_hitwh.controller.mapper import player_and_wind_mapping, game_state_mapping, datetime_format
from ml_hitwh.controller.utils import get_user_name
from ml_hitwh.model.enums import GameState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.user import UserOrm


async def map_game(io: TextIO, game: GameOrm, bot: Bot, *, map_promoter: bool = False):
    session = data_source.session()

    stmt = select(GameOrm).where(GameOrm.id == game.id).limit(1).options(
        selectinload(GameOrm.season),
        selectinload(GameOrm.promoter),
        selectinload(GameOrm.group),
        selectinload(GameOrm.records).joinedload(GameRecordOrm.user)
    )
    game: GameOrm = (await session.execute(stmt)).scalar_one_or_none()

    # 对局22090901  四人南
    io.write('对局')
    io.write(str(game.code))
    io.write('  ')
    io.write(player_and_wind_mapping[game.player_and_wind])
    io.write('\n')

    # 所属赛季：Season Name
    io.write('所属赛季：')
    if game.season_id is None:
        io.write('无')
    else:
        # season = await session.get(SeasonOrm, game.season_id)
        io.write(game.season.name)
    io.write('\n')

    if map_promoter:
        # promoter = await session.get(UserOrm, game.promoter_user_id)
        io.write('创建者：')
        io.write(game.promoter.nickname or
                 await get_user_name(game.promoter.binding_qq, game.group.binding_qq, bot))
        io.write('\n')

    # 状态：未完成
    io.write('状态：')
    io.write(game_state_mapping[GameState(game.state)])
    io.write('\n')

    if game.complete_time is not None:
        io.write('完成时间：')
        io.write(game.complete_time.strftime(datetime_format))
        io.write('\n')

    if len(game.records) > 0:
        # [空行]
        io.write('\n')

        # #1  Player Name    10000  (+5)
        # [...]
        for i, r in enumerate(sorted(game.records, key=lambda r: r.point, reverse=True)):
            # user = await session.get(UserOrm, r.user_id)
            name = r.user.nickname or await get_user_name(r.user.binding_qq, game.group.binding_qq, bot)
            io.write('#')
            io.write(str(i + 1))
            io.write('  ')
            io.write(name)
            io.write('    ')
            io.write(str(r.score))

            if game.state == GameState.completed:
                io.write('  (')
                if r.point > 0:
                    io.write('+')
                elif r.point == 0:
                    io.write('±')
                io.write(str(r.point))
                io.write(')')

            io.write('\n')


async def map_user_recent_games_as_forward_msg(games: Iterable[GameOrm], group: GroupOrm, user: UserOrm, bot: Bot):
    member_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
    return await map_games_as_forward_msg(games, bot, header=Message([
        MessageSegment.text("以下是"),
        MessageSegment("at", {"qq": user.binding_qq, "name": member_info["nickname"]}),
        MessageSegment.text("的最近对局")
    ]))


async def map_group_recent_games_as_forward_msg(games: Iterable[GameOrm], bot: Bot):
    return await map_games_as_forward_msg(games, bot, header=f"以下是本群的最近对局")


async def map_user_uncompleted_games_as_forward_msg(games: Iterable[GameOrm], group: GroupOrm, user: UserOrm, bot: Bot):
    member_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
    return await map_games_as_forward_msg(games, bot, header=Message([
        MessageSegment.text("以下是"),
        MessageSegment("at", {"qq": user.binding_qq, "name": member_info["nickname"]}),
        MessageSegment.text("的未完成对局")
    ]))


async def map_group_uncompleted_games_as_forward_msg(games: Iterable[GameOrm], bot: Bot):
    return await map_games_as_forward_msg(games, bot, header=f"以下是本群的未完成对局")


async def map_games_as_forward_msg(games: Iterable[GameOrm], bot: Bot,
                                   *, header: Optional[Union[str, Message]] = None):
    self_info = await bot.get_login_info()

    msg_li = []

    if header is not None:
        msg_li.append({
            "type": "node",
            "data": {
                "uin": bot.self_id,
                "name": self_info["nickname"],
                "content": header
            }
        })

    for g in games:
        with StringIO() as sio:
            await map_game(sio, g, bot, map_promoter=True)

            msg_li.append({
                "type": "node",
                "data": {
                    "uin": bot.self_id,
                    "name": self_info["nickname"],
                    "content": sio.getvalue()
                }
            })

    return msg_li
