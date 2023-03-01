from io import StringIO

from nonebot.adapters.onebot.v11 import MessageSegment, Message

from nonebot_plugin_mahjong_scoreboard.controller.mapper import player_and_wind_mapping, game_state_mapping, \
    digit_mapping, \
    wind_mapping, map_datetime, map_point
from nonebot_plugin_mahjong_scoreboard.model.enums import GameState
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm, GameProgressOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname
from nonebot_plugin_mahjong_scoreboard.utils.rank import ranked


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
        io.write(f'对局{game.code}  {player_and_wind_mapping[game.player_and_wind]}\n')

        if detailed:
            # 所属赛季：Season Name
            season_name = '无'
            if game.season_id is not None:
                season = await session.get(SeasonOrm, game.season_id)
                season_name = season.name
            io.write(f'所属赛季：{season_name}\n')

            promoter = await session.get(UserOrm, game.promoter_user_id)
            io.write(f'创建者：{await get_user_nickname(promoter, group)}\n')

        # 状态：未完成
        io.write(f'状态：{game_state_mapping[GameState(game.state)]}')
        if game.state != GameState.completed:
            sum_score = sum(map(lambda r: r.score, game.records))
            io.write(f"  （合计{sum_score}点）")
        io.write('\n')

        if detailed and game.state == GameState.completed:
            io.write(f'完成时间：{map_datetime(game.complete_time)}\n')

        progress = await session.get(GameProgressOrm, game.id)
        if progress is not None:
            io.write(f'进度：{map_game_progress(progress)}\n')

        if len(game.records) > 0:
            # [空行]
            io.write('\n')

            # #1 [东]    Player Name    10000点  (+5)
            # [...]
            for rank, r in ranked(game.records, key=lambda r: r.raw_point, reverse=True):
                user = await session.get(UserOrm, r.user_id)
                name = await get_user_nickname(user, group)
                io.write(f'#{rank}')
                if r.wind is not None:
                    io.write(f' [{wind_mapping[r.wind]}]')
                io.write(f'    {name}    {r.score}点')

                if game.state == GameState.completed:
                    point_text = map_point(r.raw_point, r.point_scale)
                    io.write(f'  ({point_text})')

                io.write('\n')

        if game.comment:
            io.write('\n')
            io.write("备注：")
            io.write(game.comment)
            io.write('\n')

        return Message(MessageSegment.text(io.getvalue().strip()))
