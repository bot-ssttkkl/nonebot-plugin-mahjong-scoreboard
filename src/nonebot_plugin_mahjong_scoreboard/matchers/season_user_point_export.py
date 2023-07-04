from datetime import datetime
from io import StringIO

import tzlocal
from mahjong_scoreboard_model import Season, SeasonState
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot_plugin_gocqhttp_cross_machine_upload_file import upload_file

from .interceptor import handle_error
from .mapper.season_user_point_csv_mapper import write_season_user_point_change_logs_csv
from .mg import matcher_group
from .utils.dep import SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id
from ..errors import ResultError
from ..service.season_user_point_service import get_season_user_point_change_logs
from ..utils.date import encode_date
from ..utils.nonebot import default_cmd_start

# ========== 导出榜单 ==========
export_season_ranking_matcher = matcher_group.on_command("导出榜单", priority=5)
export_season_ranking_matcher.__help_info__ = f"{default_cmd_start}导出榜单 [<赛季代号>]"

require_store_command_args(export_season_ranking_matcher)
require_platform_group_id(export_season_ranking_matcher)


@export_season_ranking_matcher.handle()
@handle_error()
async def export_season_ranking(bot: Bot, event: MessageEvent,
                                season: Season = SeasonFromUnaryArgOrRunningSeason()):
    logs = await get_season_user_point_change_logs(season.id)

    if len(logs) == 0:
        raise ResultError("还没有用户参与该赛季")

    filename = f"赛季榜单 {season.name}"
    if season.state == SeasonState.finished:
        filename += "（已结束）"
    else:
        now = datetime.now(tzlocal.get_localzone())
        filename += f"（截至{encode_date(now)}）"
    filename += ".csv"

    with StringIO() as sio:
        await write_season_user_point_change_logs_csv(sio, logs, season)

        data = sio.getvalue().encode("utf_8_sig")
        await upload_file(bot, event, filename, data)
