import csv
from datetime import date, datetime, tzinfo, time, timedelta
from typing import Awaitable, Callable

from beanie.odm.enums import SortDirection

from ml_hitwh.model.game import Game, GameState

__all__ = ("write_games_as_csv",)


async def write_games_as_csv(f, start_date: date, end_date: date, tz: tzinfo,
                             user_id_mapper: Callable[[int], Awaitable[str]]):
    start_time = datetime.combine(start_date, time(0, 0, 0, 0), tz)
    end_time = datetime.combine(end_date, time(0, 0, 0, 0), tz) + timedelta(days=1)

    writer = csv.writer(f)
    writer.writerow(['', '对局编号', '对局类型', '对局时间',
                     '一位ID', '一位分数', '一位PT收支',
                     '二位ID', '二位分数', '二位PT收支',
                     '三位ID', '三位分数', '三位PT收支',
                     '四位ID', '四位分数', '四位PT收支', ])
    counter = 1
    async for g in Game.find(Game.state == GameState.completed,
                             start_time <= Game.create_time,
                             Game.create_time < end_time,
                             sort=[("create_time", SortDirection.DESCENDING)]):
        row = [
            counter, g.game_id, g.game_type_text,
            g.create_time.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
        ]
        for i in range(len(g.record)):
            row.extend([f"{await user_id_mapper(g.record[i].user_id)} ({g.record[i].user_id})",
                        g.record[i].score,
                        g.record[i].point])

        writer.writerow(row)
        counter += 1
