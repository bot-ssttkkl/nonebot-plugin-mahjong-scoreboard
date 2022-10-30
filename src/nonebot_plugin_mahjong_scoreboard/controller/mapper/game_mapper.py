from io import StringIO

from nonebot.adapters.onebot.v11 import MessageSegment, Message

from nonebot_plugin_mahjong_scoreboard.controller.mapper import player_and_wind_mapping, game_state_mapping, \
    datetime_format, digit_mapping, \
    wind_mapping
from nonebot_plugin_mahjong_scoreboard.model.enums import GameState
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm, GameProgressOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname


def map_game_progress(progress: GameProgressOrm) -> str:
    with StringIO() as io:
        if progress.round <= 4:
            io.write('东')
            io.write(digit_mapping[progress.round])
        else:
            io.write('南')
            io.write(digit_mapping[progress.round - 4])
        io.write('局')
        io.write(str(progress.honba))
        io.write('本场')

        return io.getvalue()


async def map_game(game: GameOrm, *, detailed: bool = False) -> Message:
    session = data_source.session()

    group = await session.get(GroupOrm, game.group_id)

    with StringIO() as io:
        # 对局22090901  四人南
        io.write('对局')
        io.write(str(game.code))
        io.write('  ')
        io.write(player_and_wind_mapping[game.player_and_wind])
        io.write('\n')

        if detailed:
            # 所属赛季：Season Name
            io.write('所属赛季：')
            if game.season_id is None:
                io.write('无')
            else:
                season = await session.get(SeasonOrm, game.season_id)
                io.write(season.name)
            io.write('\n')

            promoter = await session.get(UserOrm, game.promoter_user_id)
            io.write('创建者：')
            io.write(await get_user_nickname(promoter, group))
            io.write('\n')

        # 状态：未完成
        io.write('状态：')
        io.write(game_state_mapping[GameState(game.state)])
        if game.state == GameState.invalid_total_point:
            io.write("  （合计")
            io.write(str(sum(map(lambda r: r.score, game.records))))
            io.write("点）")
        io.write('\n')

        if detailed and game.state == GameState.completed:
            io.write('完成时间：')
            io.write(game.complete_time.strftime(datetime_format))
            io.write('\n')

        progress = await session.get(GameProgressOrm, game.id)
        if progress is not None:
            io.write('进度：')
            io.write(map_game_progress(progress))
            io.write('\n')

        if len(game.records) > 0:
            # [空行]
            io.write('\n')

            # #1 [东]    Player Name    10000  (+5)
            # [...]
            for i, r in enumerate(sorted(game.records, key=lambda r: (r.point, r.score), reverse=True)):
                user = await session.get(UserOrm, r.user_id)
                name = await get_user_nickname(user, group)
                io.write('#')
                io.write(str(i + 1))
                if r.wind is not None:
                    io.write(' [')
                    io.write(wind_mapping[r.wind])
                    io.write(']')
                io.write('    ')
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

        if game.comment:
            io.write('\n')
            io.write("备注：")
            io.write(game.comment)
            io.write('\n')

        return Message(MessageSegment.text(io.getvalue().strip()))
