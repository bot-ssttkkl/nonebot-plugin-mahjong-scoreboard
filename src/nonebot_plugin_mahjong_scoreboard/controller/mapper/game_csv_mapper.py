import csv
from typing import TextIO, Iterable

from nonebot_plugin_mahjong_scoreboard.controller.mapper import datetime_format, game_state_mapping, \
    player_and_wind_mapping
from nonebot_plugin_mahjong_scoreboard.controller.mapper.game_mapper import map_game_progress
from nonebot_plugin_mahjong_scoreboard.model.enums import GameState
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm, GameProgressOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname


async def map_games_as_csv(f: TextIO, games: Iterable[GameOrm]):
    session = data_source.session()

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
            row.append(g.complete_time.strftime(datetime_format))

        group = await session.get(GroupOrm, g.group_id)

        if g.season_id is not None:
            season = await session.get(SeasonOrm, g.season_id)
            row.append(season.name)
        else:
            row.append("")

        if g.promoter_user_id is not None:
            promoter = await session.get(UserOrm, g.promoter_user_id)
            row.append(f"{await get_user_nickname(promoter, group)} ({promoter.binding_qq})")
        else:
            row.append("")

        for r in sorted(g.records, key=lambda x: x.point, reverse=True):
            user = await session.get(UserOrm, r.user_id)
            row.extend([f"{await get_user_nickname(user, group)} ({user.binding_qq})",
                        r.score,
                        r.point])

        progress = await session.get(GameProgressOrm, g.id)
        if progress is not None:
            row.append(map_game_progress(progress))
        else:
            row.append("")

        row.append(g.comment)

        writer.writerow(row)
