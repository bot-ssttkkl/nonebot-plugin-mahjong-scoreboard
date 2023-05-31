import csv
from typing import TextIO, Iterable

from nonebot.internal.matcher import current_bot

from nonebot_plugin_mahjong_scoreboard.controller.mapper import game_state_mapping, \
    player_and_wind_mapping, map_datetime, map_point
from nonebot_plugin_mahjong_scoreboard.controller.mapper.game_mapper import map_game_progress
from nonebot_plugin_mahjong_scoreboard.model import Game
from nonebot_plugin_mahjong_scoreboard.model.enums import GameState
from nonebot_plugin_mahjong_scoreboard.platform.get_user_nickname import get_user_nickname
from nonebot_plugin_mahjong_scoreboard.utils.session import get_real_id


async def write_games_csv(f: TextIO, games: Iterable[Game]):
    bot = current_bot.get()

    writer = csv.writer(f)
    writer.writerow(['对局编号', '对局类型', '状态', '完成时间',
                     '所属赛季', '发起者',
                     '一位', '一位分数', '一位PT收支',
                     '二位', '二位分数', '二位PT收支',
                     '三位', '三位分数', '三位PT收支',
                     '四位', '四位分数', '四位PT收支',
                     '进度', '备注'])
    for g in games:
        row = [
            g.code, player_and_wind_mapping[g.player_and_wind],
            game_state_mapping[g.state],
        ]

        if g.state == GameState.completed:
            row.append(map_datetime(g.complete_time))
        else:
            row.append("")

        if g.season is not None:
            row.append(g.season.name)
        else:
            row.append("")

        if g.promoter is not None:
            row.append(f"{await get_user_nickname(bot, g.promoter.platform_user_id, g.group.platform_group_id)}"
                       f" ({get_real_id(g.promoter.platform_user_id)})")
        else:
            row.append("")

        for r in sorted(g.records, key=lambda x: x.raw_point, reverse=True):
            row.extend([f"{await get_user_nickname(bot, r.user.platform_user_id, g.group.platform_group_id)}"
                        f" ({get_real_id(r.user.platform_user_id)})",
                        r.score,
                        map_point(r.raw_point, r.point_scale)])

        if g.progress is not None:
            row.append(map_game_progress(g.progress))
        else:
            row.append("")

        row.append(g.comment)

        writer.writerow(row)
