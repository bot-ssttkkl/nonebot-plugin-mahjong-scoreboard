from datetime import datetime
from io import StringIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.file_center import send_group_file, send_private_file
from ml_hitwh.controller.interceptor import workflow_interceptor, general_interceptor
from ml_hitwh.controller.mapper.game_csv_mapper import map_games_as_csv
from ml_hitwh.controller.general_handlers import require_group_binding_qq, require_unary_text
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import SeasonState
from ml_hitwh.service import season_service
from ml_hitwh.service.game_service import get_season_games, get_group_games
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.utils.date import encode_date

# ========== 导出赛季对局 ==========
export_season_games_matcher = on_command("导出赛季对局", aliases={"导出对局"}, priority=5)

require_unary_text(export_season_games_matcher, "season_code",
                   decorator=general_interceptor(export_season_games_matcher))
require_group_binding_qq(export_season_games_matcher)


@export_season_games_matcher.handle()
@workflow_interceptor(export_season_games_matcher)
async def export_season_games(bot: Bot, event: MessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])

    season_code = matcher.state.get("season_code", None)
    if season_code:
        season = await season_service.get_season_by_code(season_code, group)
        if season is None:
            raise BadRequestError("找不到指定赛季")
    else:
        if group.running_season_id:
            season = await season_service.get_season_by_id(group.running_season_id)
        else:
            raise BadRequestError("当前没有运行中的赛季")

    games = await get_season_games(season)

    filename = f"赛季对局 {season.name}"
    if season.state == SeasonState.finished:
        filename += "（已结束）"
    else:
        now = datetime.now()
        filename += f"（截至{encode_date(now)}）"
    filename += ".csv"

    with StringIO() as sio:
        await map_games_as_csv(sio, games)

        data = sio.getvalue().encode("utf_8_sig")
        if isinstance(event, GroupMessageEvent):
            await send_group_file(bot, event.group_id, filename, data)
        else:
            await send_private_file(bot, event.user_id, filename, data)


# ========== 导出所有对局 ==========
export_group_games_matcher = on_command("导出所有对局", aliases={"导出群对局"}, priority=5)

require_group_binding_qq(export_group_games_matcher)


@export_group_games_matcher.handle()
@workflow_interceptor(export_group_games_matcher)
async def export_group_games(bot: Bot, event: MessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])
    games = await get_group_games(group)

    now = datetime.now()
    filename = f"所有对局（截至{encode_date(now)}）.csv"

    with StringIO() as sio:
        await map_games_as_csv(sio, games)

        data = sio.getvalue().encode("utf_8_sig")
        if isinstance(event, GroupMessageEvent):
            await send_group_file(bot, event.group_id, filename, data)
        else:
            await send_private_file(bot, event.user_id, filename, data)
