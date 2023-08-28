import re

from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from .interceptor import handle_interruption, handle_error
from .mapper.season_mapper import map_season, map_rank_point_policy
from .mg import matcher_group
from .utils.dep import GroupDep, UnaryArg, RunningSeasonDep, SenderUserDep, IsGroupAdminDep
from .utils.general_handlers import hint_for_question_flow_on_first, require_platform_group_id, \
    require_store_command_args
from .utils.parse import parse_int_or_reject
from ..errors import BadRequestError, ResultError
from ..model import Group, Season, User, SeasonConfig, SeasonState, RankPointPolicy
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


@new_season_matcher.got("point_precision", "PT精度？（输入x，则精度为10^x。例如：输入0，保留整数部分；输入-1，保留小数点后一位）")
@handle_error()
@handle_interruption()
async def new_season_got_point_precision(matcher: Matcher,
                                         raw_arg=ArgPlainText("point_precision")):
    precision = await parse_int_or_reject(raw_arg, "PT精度", max=4, min=-1)
    matcher.state["point_precision"] = precision


@new_season_matcher.got("rank_point_policy",
                        "顺位PT策略？通过空格分割\n" +
                        "\n".join(map(lambda x: f"{x[0] + 1}. {map_rank_point_policy(x[1], with_description=True)}",
                                      enumerate(list(RankPointPolicy)))))
@handle_error()
@handle_interruption()
async def new_season_got_rank_point_policy(matcher: Matcher,
                                           raw_arg=ArgPlainText("rank_point_policy")):
    try:
        li = list(map(int, raw_arg.split(' ')))
    except ValueError:
        await matcher.reject("输入的顺位点策略不合法。请重新输入")
        return

    policy = 0

    for x in li:
        if x < 1 or x > 4:
            await matcher.reject("输入的顺位点策略不合法。请重新输入")
        policy |= 1 << (x - 1)

    if policy & RankPointPolicy.absolute_rank_point and policy != RankPointPolicy.absolute_rank_point:
        await matcher.reject("输入的顺位点策略不合法（绝对顺位点与其他策略互斥）。请重新输入")

    if policy & RankPointPolicy.overwater and policy != RankPointPolicy.overwater:
        await matcher.reject("输入的顺位点策略不合法（水上顺位点与其他策略互斥）。请重新输入")

    matcher.state["rank_point_policy"] = policy


def config(game_type: str, game_type_prompt: str):
    @new_season_matcher.got(f"{game_type}_game_enabled", f"是否开启{game_type_prompt}战？(y/n)")
    @handle_error()
    @handle_interruption()
    async def new_season_got_game_enabled(matcher: Matcher,
                                          event: Event,
                                          raw_arg=ArgPlainText(f"{game_type}_game_enabled")):
        Message = type(event.get_message())
        if raw_arg == 'y':
            matcher.state[f"{game_type}_game_enabled"] = True

            policy = matcher.state["rank_point_policy"]
            if not (policy & RankPointPolicy.absolute_rank_point) and not (policy & RankPointPolicy.horse_point):
                # 无绝对顺位点与马点时不询问顺位点
                matcher.set_arg(f"{game_type}_game_horse_point", Message())
                matcher.state[f"{game_type}_game_horse_point_skip"] = True
            if not (policy & RankPointPolicy.overwater):
                # 无水上顺位点时不询问水上顺位点
                matcher.set_arg(f"{game_type}_game_overwater_point", Message())
                matcher.state[f"{game_type}_game_overwater_point_skip"] = True
        else:
            matcher.state[f"{game_type}_game_enabled"] = False

            # 跳过询问
            matcher.set_arg(f"{game_type}_game_initial_point", Message())
            matcher.set_arg(f"{game_type}_game_origin_point", Message())
            matcher.set_arg(f"{game_type}_game_horse_point", Message())
            matcher.set_arg(f"{game_type}_game_overwater_point", Message())

    @new_season_matcher.got(f"{game_type}_game_initial_point", f"{game_type_prompt}战起点？")
    @handle_error()
    @handle_interruption()
    async def new_season_got_game_initial_point(matcher: Matcher,
                                                raw_arg=ArgPlainText(f"{game_type}_game_initial_point")):
        if not matcher.state[f"{game_type}_game_enabled"]:
            matcher.state[f"{game_type}_game_initial_point"] = None
            return

        pt = await parse_int_or_reject(raw_arg, f"{game_type_prompt}战起点")
        matcher.state[f"{game_type}_game_initial_point"] = pt

    @new_season_matcher.got(f"{game_type}_game_origin_point",
                            f"{game_type_prompt}战返点？"
                            "（若启用了头名赏策略，多于起点的部分将作为头名赏）")
    @handle_error()
    @handle_interruption()
    async def new_season_got_game_origin_point(matcher: Matcher,
                                               raw_arg=ArgPlainText(f"{game_type}_game_origin_point")):
        if not matcher.state[f"{game_type}_game_enabled"]:
            matcher.state[f"{game_type}_game_origin_point"] = None
            return

        pt = await parse_int_or_reject(raw_arg, f"{game_type_prompt}战返点",
                                       min=matcher.state[f"{game_type}_game_initial_point"])
        matcher.state[f"{game_type}_game_origin_point"] = pt

    @new_season_matcher.got(f"{game_type}_game_horse_point", f"{game_type_prompt}战顺位点？通过空格分割")
    @handle_error()
    @handle_interruption()
    async def new_season_got_game_horse_point(matcher: Matcher,
                                              raw_arg=ArgPlainText(f"{game_type}_game_horse_point")):
        if not matcher.state[f"{game_type}_game_enabled"] or matcher.state.get(f"{game_type}_game_horse_point_skip"):
            return

        try:
            li = list(map(float, raw_arg.split(' ')))
        except ValueError:
            await matcher.reject(f"输入的{game_type_prompt}战顺位点不合法。请重新输入")
            return

        if len(li) != 4:
            await matcher.reject(f"输入的{game_type_prompt}战顺位点不合法。请重新输入")

        scale = 10 ** -matcher.state["point_precision"]
        matcher.state[f"{game_type}_game_horse_point"] = [
            x * scale
            for x in li
        ]

    @new_season_matcher.got(f"{game_type}_game_overwater_point",
                            f"{game_type_prompt}战水上顺位点？通过空格分割\n"
                            f"以30000分为基准，30000分以上为水上，30000分以下为水下。"
                            f"分别输入水上人数为0人时一二三四位的顺位点、为1人时一二三四位的顺位点、"
                            f"为2人时一二三四位的顺位点、为3人时一二三四位的顺位点。（共16个数字）")
    @handle_error()
    @handle_interruption()
    async def new_season_got_game_overwater_point(matcher: Matcher,
                                                  raw_arg=ArgPlainText(f"{game_type}_game_overwater_point")):
        if not matcher.state[f"{game_type}_game_enabled"] or matcher.state.get(
                f"{game_type}_game_overwater_point_skip"):
            return

        try:
            li = list(map(float, raw_arg.split(' ')))
        except ValueError:
            await matcher.reject(f"输入的{game_type_prompt}战水上顺位点不合法。请重新输入")
            return

        if len(li) != 16:
            await matcher.reject(f"输入的{game_type_prompt}战水上顺位点不合法。请重新输入")

        scale = 10 ** -matcher.state["point_precision"]
        matcher.state[f"{game_type}_game_overwater_point"] = [
            [li[i] * scale, li[i + 1] * scale, li[i + 2] * scale, li[i + 3] * scale]
            for i in range(0, 16, 4)
        ]


config("south", "半庄")
config("east", "东风")


@new_season_matcher.handle()
@handle_error()
@handle_interruption()
async def new_season_confirm(matcher: Matcher, group: Group = GroupDep()):
    matcher.state["season_config"] = SeasonConfig(
        rank_point_policy=matcher.state["rank_point_policy"],
        south_game_enabled=matcher.state["south_game_enabled"],
        south_game_initial_point=matcher.state.get("south_game_initial_point"),
        south_game_origin_point=matcher.state.get("south_game_origin_point"),
        south_game_horse_point=matcher.state.get("south_game_horse_point"),
        south_game_overwater_point=matcher.state.get("south_game_overwater_point"),
        east_game_enabled=matcher.state["east_game_enabled"],
        east_game_initial_point=matcher.state.get("east_game_initial_point"),
        east_game_origin_point=matcher.state.get("east_game_origin_point"),
        east_game_horse_point=matcher.state.get("east_game_horse_point"),
        east_game_overwater_point=matcher.state.get("east_game_overwater_point"),
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
