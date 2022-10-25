from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import workflow_interceptor
from ml_hitwh.controller.mapper.season_mapper import map_season
from ml_hitwh.controller.workflow_general import require_group_binding_qq
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.service import season_service
from ml_hitwh.service.group_service import get_group_by_binding_qq

# ========== 新赛季 ==========
new_season_matcher = on_command("新建赛季", aliases={"新赛季"}, priority=5)

require_group_binding_qq(new_season_matcher, True)


@new_season_matcher.got("code", "赛季代号？")
@workflow_interceptor(new_season_matcher)
async def new_season_got_code(matcher: Matcher,
                              raw_arg=ArgPlainText("code")):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])
    season = await season_service.get_season_by_code(raw_arg, group)
    if season is not None:
        await matcher.reject("该赛季代号已被使用。请重新输入")

    matcher.state["code"] = raw_arg


@new_season_matcher.got("name", "赛季名称？")
@workflow_interceptor(new_season_matcher)
async def new_season_got_name(matcher: Matcher,
                              raw_arg=ArgPlainText("name")):
    matcher.state["name"] = raw_arg


@new_season_matcher.got("south_game_enabled", "是否开启半庄战？(y/n)")
async def new_season_got_east_game_enabled(matcher: Matcher,
                                           raw_arg=ArgPlainText("south_game_enabled")):
    if raw_arg == 'y':
        matcher.state["south_game_enabled"] = True
    else:
        matcher.state["south_game_enabled"] = False
        matcher.set_arg("south_game_horse_point", Message())


@new_season_matcher.got("south_game_horse_point", "半庄战马点？通过空格分割")
@workflow_interceptor(new_season_matcher)
async def new_season_got_south_game_horse_point(matcher: Matcher,
                                                raw_arg=ArgPlainText("south_game_horse_point")):
    if not matcher.state["south_game_enabled"]:
        return

    try:
        li = list(map(int, raw_arg.split(' ')))
    except ValueError:
        await matcher.reject("输入的半庄战马点不合法。请重新输入")
        return

    if len(li) != 4:
        await matcher.reject("输入的半庄战马点不合法。请重新输入")
    matcher.state["south_game_horse_point"] = li


@new_season_matcher.got("east_game_enabled", "是否开启东风战？(y/n)")
async def new_season_got_east_game_enabled(matcher: Matcher,
                                           raw_arg=ArgPlainText("east_game_enabled")):
    if raw_arg == 'y':
        matcher.state["east_game_enabled"] = True
    else:
        matcher.state["east_game_enabled"] = False
        matcher.set_arg("east_game_horse_point", Message())

    if not matcher.state["south_game_enabled"] and not matcher.state["east_game_enabled"]:
        raise BadRequestError("半庄战、东风战至少需要开启一种")


@new_season_matcher.got("east_game_horse_point", "东风战马点？通过空格分割")
@workflow_interceptor(new_season_matcher)
async def new_season_got_east_game_horse_point(matcher: Matcher,
                                               raw_arg=ArgPlainText("east_game_horse_point")):
    if not matcher.state["east_game_enabled"]:
        return

    try:
        li = list(map(int, raw_arg.split(' ')))
    except ValueError:
        await matcher.reject("输入的东风战马点不合法。请重新输入")
        return

    if len(li) != 4:
        await matcher.reject("输入的东风战马点不合法。请重新输入")
    matcher.state["east_game_horse_point"] = li


@new_season_matcher.handle()
@workflow_interceptor(new_season_matcher)
async def new_season_confirm(matcher: Matcher):
    season = SeasonOrm(code=matcher.state["code"],
                       name=matcher.state["name"],
                       south_game_enabled=matcher.state["south_game_enabled"],
                       south_game_horse_point=matcher.state["south_game_horse_point"],
                       east_game_enabled=matcher.state["east_game_enabled"],
                       east_game_horse_point=matcher.state["east_game_horse_point"])
    matcher.state["season"] = season

    msg = map_season(season, group_info=matcher.state["group_info"])
    msg.append(MessageSegment.text("\n确定创建赛季吗？(y/n)"))
    await matcher.pause(msg)


@new_season_matcher.handle()
@workflow_interceptor(new_season_matcher)
async def new_season_handle(event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        season = matcher.state["season"]
        season.group = await get_group_by_binding_qq(matcher.state["binding_qq"])
        season = await season_service.new_season(season)
        matcher.state["season_id"] = season.id
        await matcher.pause("赛季创建成功。是否立刻开启该赛季？(y/n)")
    else:
        await matcher.finish("取消赛季创建")


@new_season_matcher.handle()
@workflow_interceptor(new_season_matcher)
async def new_season_start(event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        # 因为session不同，所以需要重新获取season
        season = await season_service.get_season_by_id(matcher.state["season_id"])
        await season_service.start_season(season)
        await matcher.send("赛季开启成功")
    else:
        await matcher.send("稍后可以使用“/开启赛季”命令开启赛季")


# ========== 开启赛季 ==========
start_season_matcher = on_command("开启赛季", priority=5)

require_group_binding_qq(start_season_matcher, True)


@start_season_matcher.got("code", "赛季代号？")
@workflow_interceptor(start_season_matcher)
async def start_season_matcher_got_code(matcher: Matcher,
                                        raw_arg=ArgPlainText("code")):
    season = await season_service.get_season_by_code(raw_arg, matcher.state["group"])
    if season is None:
        raise BadRequestError("找不到赛季。使用“/新赛季”指令创建赛季")

    matcher.state["season"] = season
    matcher.state["season_id"] = season.id


@start_season_matcher.handle()
@workflow_interceptor(start_season_matcher)
async def start_season_confirm(matcher: Matcher):
    season = matcher.state["season"]

    msg = map_season(season, group_info=matcher.state["group_info"])
    msg.append(MessageSegment.text("\n确定开启赛季吗？(y/n)"))
    await matcher.pause(msg)


@start_season_matcher.handle()
@workflow_interceptor(start_season_matcher)
async def start_season_end(event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        # 因为session不同，所以需要重新获取season
        season = await season_service.get_season_by_id(matcher.state["season_id"])
        await season_service.start_season(season)
        await matcher.send("赛季开启成功")
    else:
        await matcher.send("取消开启赛季")


# ========== 结束赛季 ==========
finish_season_matcher = on_command("结束赛季", priority=5)

require_group_binding_qq(finish_season_matcher, True)


@finish_season_matcher.handle()
@workflow_interceptor(finish_season_matcher)
async def finish_season_confirm(matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])
    season = await season_service.get_season_by_id(group.running_season_id)
    matcher.state["season_id"] = season.id

    if season is None:
        raise BadRequestError("当前没有运行中的赛季")

    msg = map_season(season, group_info=matcher.state["group_info"])
    msg.append(MessageSegment.text("\n确定结束赛季吗？(y/n)"))
    await matcher.pause(msg)


@finish_season_matcher.handle()
@workflow_interceptor(finish_season_matcher)
async def finish_season_end(event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        # 因为session不同，所以需要重新获取season
        season = await season_service.get_season_by_id(matcher.state["season_id"])
        await season_service.finish_season(season)
        await matcher.send("赛季结束成功")
    else:
        await matcher.send("取消结束赛季")
