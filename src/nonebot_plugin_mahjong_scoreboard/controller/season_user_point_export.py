from datetime import datetime
from io import StringIO

import tzlocal
from ssttkkl_nonebot_utils.errors.errors import QueryError
from ssttkkl_nonebot_utils.interceptor.handle_error import handle_error

from .mapper.season_user_point_csv_mapper import write_season_user_point_change_logs_csv
from .mg import matcher_group
from .utils.dep import SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id
from .utils.send_csv import send_csv
from ..model import Season, SeasonState
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
async def export_season_ranking(season: Season = SeasonFromUnaryArgOrRunningSeason()):
    logs = await get_season_user_point_change_logs(season.id)

    if len(logs) == 0:
        raise QueryError("还没有用户参与该赛季")

    filename = f"赛季榜单 {season.name}"
    if season.state == SeasonState.finished:
        filename += "（已结束）"
    else:
        now = datetime.now(tzlocal.get_localzone())
        filename += f"（截至{encode_date(now)}）"
    filename += ".csv"

    with StringIO() as sio:
        await write_season_user_point_change_logs_csv(sio, logs, season)
        sio.seek(0)
        await send_csv(sio, filename)
