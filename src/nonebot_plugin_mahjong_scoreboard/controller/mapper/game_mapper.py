from io import StringIO

from nonebot.internal.matcher import current_bot

from . import player_and_wind_mapping, game_state_mapping, digit_mapping, wind_mapping, map_datetime, map_point
from ...model import Game, GameProgress
from ...model.enums import GameState
from ...platform import func
from ...utils.rank import ranked


def map_game_progress(progress: GameProgress) -> str:
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


async def map_game(game: Game, *, detailed: bool = False) -> str:
    bot = current_bot.get()
    with StringIO() as io:
        # 对局22090901  四人南
        io.write(f'对局{game.code}  {player_and_wind_mapping[game.player_and_wind]}\n')

        if detailed:
            # 所属赛季：Season Name
            season_name = '无'
            if game.season is not None:
                season_name = game.season.name
            io.write(f'所属赛季：{season_name}\n')

            io.write(
                f'创建者：{await func(bot).get_user_nickname(bot, game.promoter.platform_user_id, game.group.platform_group_id)}\n')

        # 状态：未完成
        io.write(f'状态：{game_state_mapping[game.state]}')
        if game.state != GameState.completed:
            sum_score = sum(map(lambda r: r.score, game.records))
            io.write(f"  （合计{sum_score}点）")
        io.write('\n')

        if detailed and game.state == GameState.completed:
            io.write(f'完成时间：{map_datetime(game.complete_time)}\n')

        if game.progress is not None:
            io.write(f'进度：{map_game_progress(game.progress)}\n')

        if len(game.records) > 0:
            # [空行]
            io.write('\n')

            # #1 [东]    Player Name    10000点  (+5)
            # [...]
            for rank, r in ranked(game.records, key=lambda r: r.raw_point, reverse=True):
                io.write(f'#{rank}')
                if r.wind is not None:
                    io.write(f' [{wind_mapping[r.wind]}]')
                io.write(f'    {await func(bot).get_user_nickname(bot, r.user.platform_user_id, game.group.platform_group_id)}'
                         f'    {r.score}点')

                if game.state == GameState.completed:
                    point_text = map_point(r.raw_point, r.point_scale)
                    io.write(f'  ({point_text})')

                io.write('\n')

        if game.comment:
            io.write('\n')
            io.write("备注：")
            io.write(game.comment)
            io.write('\n')

        return io.getvalue().strip()


async def map_game_lite(game: Game) -> str:
    bot = current_bot.get()
    with StringIO() as io:
        # 对局23060101 [已完成]  Player Name(+5)  Player Name(+5)  Player Name(+5)  Player Name(+5)
        io.write(f"对局{game.code}  ")

        if game.progress is not None:
            io.write(f"[{map_game_progress(game.progress)}]")
        else:
            io.write(f"[{game_state_mapping[game.state]}]")

        for r in sorted(game.records, key=lambda r: r.raw_point, reverse=True):
            io.write("  ")
            if r.wind is not None:
                io.write(f"[{wind_mapping[r.wind]}]")
            io.write(f"{await func(bot).get_user_nickname(bot, r.user.platform_user_id, game.group.platform_group_id)}")
            if game.state == GameState.completed:
                io.write(f"({map_point(r.raw_point, r.point_scale)})")
            else:
                io.write(f"({r.score}点)")

        return io.getvalue().strip()
