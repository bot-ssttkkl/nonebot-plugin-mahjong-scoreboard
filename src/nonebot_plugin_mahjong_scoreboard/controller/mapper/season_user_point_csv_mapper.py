import csv
from typing import TextIO, Iterable, List

from nonebot.internal.matcher import current_bot

from nonebot_plugin_mahjong_scoreboard.controller.mapper import map_datetime, map_point
from nonebot_plugin_mahjong_scoreboard.model import Season, SeasonUserPointChangeLog, SeasonUserPointChangeType
from nonebot_plugin_mahjong_scoreboard.utils.nickname import get_user_nickname


def _ensure_size(li: list, new_size: int, default):
    while len(li) < new_size:
        li.append(default)


async def write_season_user_point_change_logs_csv(f: TextIO, logs: Iterable[SeasonUserPointChangeLog],
                                                  season: Season):
    bot = current_bot.get()

    header = ['', '合计PT']
    table: List[List[str]] = []

    user_idx = {}
    game_idx = {}

    user_point = {}
    scale = season.config.point_precision

    # 初步绘制表格
    for log in sorted(logs, key=lambda l: l.create_time):
        if log.user.id not in user_idx:
            table.append([f"{await get_user_nickname(bot, log.user.platform_user_id, season.group.platform_group_id)}"
                          f" ({log.user.platform_user_id.real_id})", ""])
            user_idx[log.user.id] = len(table) - 1

        if log.change_type == SeasonUserPointChangeType.game:
            if log.related_game.id not in game_idx:
                header.append(str(log.related_game.code))
                game_idx[log.related_game.id] = len(header) - 1

            _ensure_size(table[user_idx[log.user.id]], game_idx[log.related_game.id] + 1, '')
            table[user_idx[log.user.id]][game_idx[log.related_game.id]] = map_point(log.change_point, scale)

            user_point[log.user.id] = user_point.get(log.user.id, 0) + log.change_point
        elif log.change_type == SeasonUserPointChangeType.manually:
            header.append(f"手动设置\n{map_datetime(log.create_time)}")

            _ensure_size(table[user_idx[log.user.id]], len(header), '')
            table[user_idx[log.user.id]][-1] = map_point(log.change_point, scale)

            user_point[log.user.id] = log.change_point

    # 将行（用户）按pt排序
    ordered_user_idx = []
    for user_id, idx in user_idx.items():
        ordered_user_idx.append((user_id, idx, user_point[user_id]))
    ordered_user_idx.sort(key=lambda x: x[2], reverse=True)

    new_table = [header]
    for user_id, idx, point in ordered_user_idx:
        new_table.append(table[idx])
        table[idx][1] = map_point(point, scale)

    writer = csv.writer(f)
    writer.writerows(new_table)
