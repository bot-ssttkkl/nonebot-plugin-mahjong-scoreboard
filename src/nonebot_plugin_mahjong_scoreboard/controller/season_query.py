from io import StringIO

from nonebot.internal.matcher import Matcher

from .interceptor import handle_error
from .mapper import season_state_mapping
from .mapper.season_mapper import map_season
from .mg import matcher_group
from .utils.dep import GroupDep, SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id
from ..model import Group, Season
from ..service.season_service import get_group_seasons
from ..utils.nonebot import default_cmd_start

# ========== 查询赛季 ==========
query_season_matcher = matcher_group.on_command("查询赛季", aliases={"赛季", "当前赛季"}, priority=10)
query_season_matcher.__help_info__ = f"{default_cmd_start}查询赛季 [<代号>]"

require_store_command_args(query_season_matcher)
require_platform_group_id(query_season_matcher)


@query_season_matcher.handle()
@handle_error()
async def query_running_season(matcher: Matcher,
                               season: Season = SeasonFromUnaryArgOrRunningSeason()):
    msg = map_season(season)
    await matcher.send(msg)


# ========== 查询所有赛季 ==========
query_all_seasons_matcher = matcher_group.on_command("查询所有赛季", aliases={"所有赛季"}, priority=5)
query_all_seasons_matcher.__help_info__ = f"{default_cmd_start}查询所有赛季"

require_store_command_args(query_all_seasons_matcher)
require_platform_group_id(query_all_seasons_matcher)


@query_all_seasons_matcher.handle()
@handle_error()
async def query_all_seasons(matcher: Matcher, group: Group = GroupDep()):
    seasons = await get_group_seasons(group.id)

    if len(seasons) != 0:
        with StringIO() as sio:
            sio.write("以下是本群的所有赛季：\n")
            for s in seasons:
                sio.write(f"  {s.name}（{s.code}）   {season_state_mapping[s.state]}")

            await matcher.send(sio.getvalue().strip())
    else:
        await matcher.send("本群还没有创建赛季")
