from io import StringIO

from nonebot.adapters.onebot.v11 import MessageSegment, Message

from ml_hitwh.controller.mapper import player_and_wind_mapping, game_state_mapping, datetime_format
from ml_hitwh.model.enums import GameState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import get_user_nickname


async def map_game(game: GameOrm, *, map_promoter: bool = False) -> Message:
    session = data_source.session()

    group = await session.get(GroupOrm, game.group_id)

    with StringIO() as io:
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
            season = await session.get(SeasonOrm, game.season_id)
            io.write(season.name)
        io.write('\n')

        if map_promoter:
            promoter = await session.get(UserOrm, game.promoter_user_id)
            io.write('创建者：')
            io.write(await get_user_nickname(promoter, group))
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
                user = await session.get(UserOrm, r.user_id)
                name = await get_user_nickname(user, group)
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

        return Message(MessageSegment.text(io.getvalue()))
