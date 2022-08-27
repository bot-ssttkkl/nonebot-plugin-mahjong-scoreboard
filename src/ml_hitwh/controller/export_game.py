from datetime import datetime, timedelta
from functools import partial
from io import StringIO

import pytz
import tzlocal
from fastapi import FastAPI, Path
from nonebot import on_command, get_app, get_bot, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from starlette.responses import Response

from ml_hitwh.controller.utils import get_user_name
from ml_hitwh.service import export_game as export_game_service
from ml_hitwh.utils import encode_date, decode_date


def make_user_id_mapper(bot_id: str, group_id: int):
    bot = get_bot(bot_id)
    return partial(get_user_name, group_id=group_id, bot=bot)


# ============ HTTP API ============

app: FastAPI = get_app()


@app.get("/api/games/{start_date}/{end_date}")
async def get_games(
        start_date: int = Path(title="start date"),
        end_date: int = Path(title="end date"),
        *, tz: str = tzlocal.get_localzone_name(),
        bot_id: str,
        group_id: int,
):
    start_date = decode_date(start_date)
    end_date = decode_date(end_date)
    tz = pytz.timezone(tz)
    user_id_mapper = make_user_id_mapper(bot_id, group_id)

    with StringIO() as sio:
        await export_game_service.write_games_as_csv(
            sio, start_date, end_date, tz,
            user_id_mapper
        )
        content = sio.getvalue().encode("utf_8_sig")

    return Response(content, media_type="text/csv")


# ============ nonebot matcher ============

export_game_matcher = on_command("导出对局", priority=5)


@export_game_matcher.handle()
async def export_game(bot: Bot, event: GroupMessageEvent):
    now = datetime.now(tzlocal.get_localzone())
    today = now.date()
    one_week_before = today + timedelta(days=-6)

    driver = get_driver()

    download_result = await bot.download_file(
        url=f"http://{driver.config.host}:{driver.config.port}/"
            f"api/games/{encode_date(one_week_before)}/{encode_date(today)}"
            f"?tz={tzlocal.get_localzone_name()}&bot_id={bot.self_id}&group_id={event.group_id}",
        thread_count=1
    )

    remote_filename = f"对局记录 {encode_date(one_week_before)}-{encode_date(today)}.csv"
    await bot.upload_group_file(group_id=event.group_id,
                                file=download_result["file"],
                                name=remote_filename)
