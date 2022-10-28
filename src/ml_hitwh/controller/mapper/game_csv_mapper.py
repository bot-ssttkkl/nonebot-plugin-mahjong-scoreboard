import csv
from typing import TextIO, Iterable

from ml_hitwh.controller.mapper import datetime_format, game_state_mapping, player_and_wind_mapping
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import get_user_nickname


async def map_games_as_csv(f: TextIO, games: Iterable[GameOrm]):
    session = data_source.session()

    writer = csv.writer(f)
    writer.writerow(['对局编号', '对局类型', '对局时间', '状态',
                     '所属赛季', '发起者',
                     '一位', '一位分数', '一位PT收支',
                     '二位', '二位分数', '二位PT收支',
                     '三位', '三位分数', '三位PT收支',
                     '四位', '四位分数', '四位PT收支', ])
    for g in games:
        row = [
            g.code, player_and_wind_mapping[g.player_and_wind],
            g.create_time.strftime(datetime_format),
            game_state_mapping[g.state]
        ]

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

        writer.writerow(row)
