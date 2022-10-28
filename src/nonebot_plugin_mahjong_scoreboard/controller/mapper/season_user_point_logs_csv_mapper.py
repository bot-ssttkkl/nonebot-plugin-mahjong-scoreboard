import csv
from typing import TextIO, Iterable, List

from nonebot_plugin_mahjong_scoreboard.controller.mapper import datetime_format
from nonebot_plugin_mahjong_scoreboard.model.enums import SeasonUserPointChangeType
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm, SeasonUserPointChangeLogOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname


def _ensure_size(li: list, new_size: int, default):
    while len(li) < new_size:
        li.append(default)


async def map_season_user_point_change_logs_as_csv(f: TextIO, logs: Iterable[SeasonUserPointChangeLogOrm],
                                                   season: SeasonOrm):
    session = data_source.session()
    group = await session.get(GroupOrm, season.group_id)

    header = ['', '合计PT']
    table: List[List[str]] = []

    user_idx = {}
    game_idx = {}

    user_point = {}

    # 初步绘制表格
    for log in logs:
        user = await session.get(UserOrm, log.user_id)
        if user.id not in user_idx:
            table.append([f"{await get_user_nickname(user, group)} ({user.binding_qq})", ""])
            user_idx[user.id] = len(table) - 1

        if log.change_type == SeasonUserPointChangeType.game:
            related_game = await session.get(GameOrm, log.related_game_id)
            if related_game.id not in game_idx:
                header.append(str(related_game.code))
                game_idx[related_game.id] = len(header) - 1

            _ensure_size(table[user_idx[user.id]], game_idx[related_game.id] + 1, '')
            table[user_idx[user.id]][game_idx[related_game.id]] = str(log.change_point)

            user_point[user.id] = user_point.get(user.id, 0) + log.change_point
        elif log.change_type == SeasonUserPointChangeType.manually:
            header.append(f"手动设置 （{log.create_time.strftime(datetime_format)}）")

            _ensure_size(table[user_idx[user.id]], len(header), '')
            table[user_idx[user.id]][-1] = str(log.change_point)

            user_point[user.id] = log.change_point

    # 将行（用户）按pt排序
    ordered_user_idx = []
    for user_id, idx in user_idx.items():
        ordered_user_idx.append((user_id, idx, user_point[user_id]))
    ordered_user_idx.sort(key=lambda x: x[2], reverse=True)

    new_table = [header]
    for user_id, idx, point in ordered_user_idx:
        new_table.append(table[idx])
        table[idx][1] = str(point)

    # # 交换行列
    # table = [[''] * len(new_table) for i in range(len(new_table[0]))]
    # for i in range(len(new_table)):
    #     for j in range(len(new_table[i])):
    #         table[j][i] = new_table[i][j]

    writer = csv.writer(f)
    writer.writerows(new_table)
