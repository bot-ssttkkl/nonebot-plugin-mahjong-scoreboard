from datetime import datetime
from io import StringIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
# ========== 导出赛季对局 ==========
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.file_center import send_group_file, send_private_file
from ml_hitwh.controller.interceptor import general_interceptor, workflow_interceptor
from ml_hitwh.controller.mapper.game_csv_mapper import map_games_as_csv
from ml_hitwh.controller.utils import split_message
from ml_hitwh.controller.workflow_general import require_group_binding_qq
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import SeasonState
from ml_hitwh.service import season_service
from ml_hitwh.service.game_service import get_season_games
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.utils import encode_date

export_season_game_matcher = on_command("导出赛季对局", aliases={"导出对局"}, priority=5)


@export_season_game_matcher.handle()
@workflow_interceptor(export_season_game_matcher)
async def export_season_game_begin(event: MessageEvent, matcher: Matcher):
    args = split_message(event.message)
    if len(args) > 1 and args[1].type == 'text':
        matcher.state["season_code"] = args[1].data["text"]


require_group_binding_qq(export_season_game_matcher)


@export_season_game_matcher.handle()
@general_interceptor(export_season_game_matcher)
async def export_season_game(bot: Bot, event: MessageEvent, matcher: Matcher):
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
