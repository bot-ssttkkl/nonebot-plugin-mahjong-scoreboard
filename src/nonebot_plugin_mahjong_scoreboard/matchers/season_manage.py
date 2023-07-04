import re

from mahjong_scoreboard_model import Group, Season, User, SeasonConfig, SeasonState
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from .interceptor import handle_interruption, handle_error
from .mapper.season_mapper import map_season
from .mg import matcher_group
from .utils.dep import GroupDep, UnaryArg, RunningSeasonDep, SenderUserDep, IsGroupAdminDep
from .utils.general_handlers import hint_for_question_flow_on_first, require_platform_group_id, \
    require_store_command_args
from .utils.parse import parse_int_or_reject
from ..errors import BadRequestError, ResultError
from ..service import season_service
from ..service.season_service import get_season_by_code, new_season, start_season, finish_season
from ..utils.nonebot import default_cmd_start

# ========== 新赛季 ==========
new_season_matcher = matcher_group.on_command("新建赛季", aliases={"新赛季"}, priority=5)
new_season_matcher.__help_info__ = f"{default_cmd_start}新建赛季"

new_season_matcher.append_handler(hint_for_question_flow_on_first)

require_platform_group_id(new_season_matcher)


@new_season_matcher.got("code", "赛季代号？")
@handle_error()
@handle_interruption()
async def new_season_got_code(matcher: Matcher,
                              raw_arg=ArgPlainText("code"),
                              group: Group = GroupDep(),
                              group_admin=IsGroupAdminDep()):
    match_result = re.match(r"[_a-zA-Z]\w*", raw_arg)
    if match_result is None:
        await matcher.reject("赛季代号不合法。请重新输入。（赛季代号只允许包含字母、数字和下划线，且必须以字母或下划线开头）")

    season = await get_season_by_code(raw_arg, group.id)
    if season is not None:
        await matcher.reject("该赛季代号已被使用。请重新输入")

    matcher.state["code"] = raw_arg


@new_season_matcher.got("name", "赛季名称？")
@handle_error()
@handle_interruption()
async def new_season_got_name(matcher: Matcher,
                              raw_arg=ArgPlainText("name")):
    matcher.state["name"] = raw_arg


@new_season_matcher.got("south_game_enabled", "是否开启半庄战？(y/n)")
@handle_error()
@handle_interruption()
async def new_season_got_east_game_enabled(matcher: Matcher,
                                           event: Event,
                                           raw_arg=ArgPlainText("south_game_enabled")):
    Message = type(event.get_message())
    if raw_arg == 'y':
        matcher.state["south_game_enabled"] = True
    else:
        matcher.state["south_game_enabled"] = False
        matcher.set_arg("south_game_origin_point", Message())
        matcher.set_arg("south_game_horse_point", Message())


@new_season_matcher.got("south_game_origin_point", "半庄战返点？")
@handle_error()
@handle_interruption()
async def new_season_got_south_game_origin_point(matcher: Matcher,
                                                 raw_arg=ArgPlainText("south_game_origin_point")):
    if not matcher.state["south_game_enabled"]:
        matcher.state["south_game_origin_point"] = None
        return

    pt = await parse_int_or_reject(raw_arg, "半庄战返点")
    matcher.state["south_game_origin_point"] = pt


@new_season_matcher.got("south_game_horse_point", "半庄战马点？通过空格分割")
@handle_error()
@handle_interruption()
async def new_season_got_south_game_horse_point(matcher: Matcher,
                                                raw_arg=ArgPlainText("south_game_horse_point")):
    if not matcher.state["south_game_enabled"]:
        return

    try:
        li = list(map(float, raw_arg.split(' ')))
    except ValueError:
        await matcher.reject("输入的半庄战马点不合法。请重新输入")
        return

    if len(li) != 4:
        await matcher.reject("输入的半庄战马点不合法。请重新输入")
    matcher.state["south_game_horse_point"] = li


@new_season_matcher.got("east_game_enabled", "是否开启东风战？(y/n)")
@handle_error()
@handle_interruption()
async def new_season_got_east_game_enabled(matcher: Matcher,
                                           event: Event,
                                           raw_arg=ArgPlainText("east_game_enabled")):
    Message = type(event.get_message())
    if raw_arg == 'y':
        matcher.state["east_game_enabled"] = True
    else:
        matcher.state["east_game_enabled"] = False
        matcher.set_arg("east_game_origin_point", Message())
        matcher.set_arg("east_game_horse_point", Message())

    if not matcher.state["south_game_enabled"] and not matcher.state["east_game_enabled"]:
        raise ResultError("半庄战、东风战至少需要开启一种")


@new_season_matcher.got("east_game_origin_point", "东风战返点？")
@handle_error()
@handle_interruption()
async def new_season_got_south_game_origin_point(matcher: Matcher,
                                                 raw_arg=ArgPlainText("east_game_origin_point")):
    if not matcher.state["east_game_enabled"]:
        matcher.state["east_game_origin_point"] = None
        return

    pt = await parse_int_or_reject(raw_arg, "东风战返点")
    matcher.state["east_game_origin_point"] = pt


@new_season_matcher.got("east_game_horse_point", "东风战马点？通过空格分割")
@handle_error()
@handle_interruption()
async def new_season_got_east_game_horse_point(matcher: Matcher,
                                               raw_arg=ArgPlainText("east_game_horse_point")):
    if not matcher.state["east_game_enabled"]:
        return

    try:
        li = list(map(float, raw_arg.split(' ')))
    except ValueError:
        await matcher.reject("输入的东风战马点不合法。请重新输入")
        return

    if len(li) != 4:
        await matcher.reject("输入的东风战马点不合法。请重新输入")
    matcher.state["east_game_horse_point"] = li


@new_season_matcher.got("point_precision",
                        "PT精度？（输入x，则精度为10^x。例如：输入0，保留整数部分；输入-1，保留小数点后一位）")
@handle_error()
@handle_interruption()
async def new_season_got_point_precision(matcher: Matcher,
                                         raw_arg=ArgPlainText("point_precision")):
    precision = await parse_int_or_reject(raw_arg, "PT精度", max=4, min=-1)
    matcher.state["point_precision"] = precision


@new_season_matcher.handle()
@handle_error()
@handle_interruption()
async def new_season_confirm(matcher: Matcher, group: Group = GroupDep()):
    matcher.state["season_config"] = SeasonConfig(
        south_game_enabled=matcher.state["south_game_enabled"],
        south_game_origin_point=matcher.state.get("south_game_origin_point"),
        south_game_horse_point=matcher.state.get("south_game_horse_point"),
        east_game_enabled=matcher.state["east_game_enabled"],
        east_game_origin_point=matcher.state.get("east_game_origin_point"),
        east_game_horse_point=matcher.state.get("east_game_horse_point"),
        point_precision=matcher.state["point_precision"]
    )

    season = Season(id=0,
                    group=group,
                    state=SeasonState.initial,
                    code=matcher.state["code"],
                    name=matcher.state["name"],
                    config=matcher.state["season_config"])

    msg = map_season(season)
    msg += "\n\n确定创建赛季吗？(y/n)"
    await matcher.pause(msg)


@new_season_matcher.handle()
@handle_error()
async def new_season_handle(event: Event, matcher: Matcher, group: Group = GroupDep()):
    if event.get_message().extract_plain_text() == 'y':
        season = await new_season(group.id, code=matcher.state["code"],
                                  name=matcher.state["name"],
                                  config=matcher.state["season_config"])
        matcher.state["season"] = season
        await matcher.pause("赛季创建成功。是否立刻开启该赛季？(y/n)")
    else:
        await matcher.finish("取消赛季创建")


@new_season_matcher.handle()
@handle_error()
async def new_season_start(event: Event, matcher: Matcher, operator: User = SenderUserDep()):
    if event.get_message().extract_plain_text() == 'y':
        await start_season(matcher.state["season"].id, operator.id)
        await matcher.send("赛季开启成功")
    else:
        await matcher.send(f"稍后可以使用“/开启赛季 {matcher.state['season'].code}”命令开启赛季")


# ========== 开启赛季 ==========
start_season_matcher = matcher_group.on_command("开启赛季", priority=5)
start_season_matcher.__help_info__ = f"{default_cmd_start}开启赛季 [<代号>]"

require_store_command_args(start_season_matcher)
require_platform_group_id(start_season_matcher)


@start_season_matcher.handle()
@handle_error()
async def start_season_matcher_confirm(matcher: Matcher, group: Group = GroupDep(),
                                       season_code=UnaryArg(),
                                       group_admin=IsGroupAdminDep()):
    if season_code is None:
        raise BadRequestError("请指定赛季编号。使用“/新赛季”指令创建赛季")

    season = await get_season_by_code(season_code, group.id)
    if season is None:
        raise ResultError("找不到该赛季。使用“/新赛季”指令创建赛季")

    matcher.state["season"] = season

    msg = map_season(season)
    if season.state != SeasonState.initial:
        msg += "\n\n赛季未处于初始状态，操作失败"
        await matcher.finish(msg)
    else:
        msg += "\n\n确定开启赛季吗？(y/n)"
        await matcher.pause(msg)


@start_season_matcher.handle()
@handle_error()
async def start_season_end(event: Event, matcher: Matcher, operator: User = SenderUserDep()):
    if event.get_message().extract_plain_text() == 'y':
        await season_service.start_season(matcher.state["season"].id, operator.id)
        await matcher.send("赛季开启成功")
    else:
        await matcher.send("取消开启赛季")


# ========== 结束赛季 ==========
finish_season_matcher = matcher_group.on_command("结束赛季", priority=5)
finish_season_matcher.__help_info__ = f"{default_cmd_start}结束赛季"

require_store_command_args(finish_season_matcher)
require_platform_group_id(finish_season_matcher)


@finish_season_matcher.handle()
@handle_error()
async def finish_season_confirm(matcher: Matcher, season: Season = RunningSeasonDep(),
                                group_admin=IsGroupAdminDep()):
    matcher.state["season"] = season
    msg = map_season(season)
    msg += "\n\n结束赛季将删除赛季的所有未完成对局，并且无法再修改赛季的已完成对局。\n确定结束赛季吗？(y/n)"
    await matcher.pause(msg)


@finish_season_matcher.handle()
@handle_error()
async def finish_season_end(event: Event, matcher: Matcher, operator: User = SenderUserDep()):
    if event.get_message().extract_plain_text() == 'y':
        await finish_season(matcher.state["season"].id, operator.id)
        await matcher.send("赛季结束成功")
    else:
        await matcher.send("取消结束赛季")


# ========== 删除赛季 ==========
remove_season_matcher = matcher_group.on_command("删除赛季", priority=5)
remove_season_matcher.__help_info__ = f"{default_cmd_start}删除赛季 [<代号>]"

require_store_command_args(remove_season_matcher)
require_platform_group_id(remove_season_matcher)


@remove_season_matcher.handle()
@handle_error()
async def remove_season_confirm(matcher: Matcher, group: Group = GroupDep(),
                                season_code=UnaryArg(),
                                group_admin=IsGroupAdminDep()):
    if season_code is None:
        raise BadRequestError("请指定赛季编号")

    season = await get_season_by_code(season_code, group.id)
    if season is None:
        raise ResultError("找不到该赛季")

    matcher.state["season"] = season

    msg = map_season(season)
    if season.state != SeasonState.initial:
        msg += "\n\n赛季未处于初始状态，操作失败"
        await matcher.finish(msg)
    else:
        msg += "\n\n确定删除赛季吗？(y/n)"
        await matcher.pause(msg)


@remove_season_matcher.handle()
@handle_error()
async def remove_season_end(event: Event, matcher: Matcher, operator: User = SenderUserDep()):
    if event.get_message().extract_plain_text() == 'y':
        await season_service.remove_season(matcher.state["season"].id, operator.id)
        await matcher.send("赛季删除成功")
    else:
        await matcher.send("取消删除赛季")
