from io import StringIO

from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import MessageEvent, Message, GroupMessageEvent, ActionFailed
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.season_mapper import map_season
from ml_hitwh.controller.utils import parse_int_or_reject
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.orm.season import SeasonOrm
from ml_hitwh.service import season_service
from ml_hitwh.service.group_service import get_group_by_binding_qq

new_season_matcher = on_command("新赛季", priority=5)


@new_season_matcher.handle()
@general_interceptor(new_season_matcher)
async def new_season_begin(bot: Bot, event: MessageEvent, matcher: Matcher):
    if isinstance(event, GroupMessageEvent):
        matcher.set_arg("binding_qq", Message(str(event.group_id)))


@new_season_matcher.got("binding_qq", "群号？")
@general_interceptor(new_season_matcher)
async def new_season_got_group_binding_qq(bot: Bot, event: MessageEvent, matcher: Matcher,
                                          raw_arg=ArgPlainText("binding_qq")):
    binding_qq = await parse_int_or_reject(raw_arg, "群号", matcher)

    try:
        group_info = await bot.get_group_info(group_id=binding_qq)
        # 如果机器人尚未加入群, group_create_time, group_level, max_member_count 和 member_count 将会为0
        if group_info["member_count"] == 0:
            raise BadRequestError("机器人尚未加入群")
        else:
            matcher.state["group_info"] = group_info
    except ActionFailed as e:
        raise BadRequestError(e.info["wording"])

    matcher.state["binding_qq"] = binding_qq


@new_season_matcher.got("code", "赛季代号？")
@general_interceptor(new_season_matcher)
async def new_season_got_code(bot: Bot, event: MessageEvent, matcher: Matcher,
                              raw_arg=ArgPlainText("code")):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])
    season = await season_service.get_season_by_code(raw_arg, group)
    if season is not None:
        await matcher.reject("该赛季代号已被使用。请重新输入")

    matcher.state["code"] = raw_arg


@new_season_matcher.got("name", "赛季名称？")
@general_interceptor(new_season_matcher)
async def new_season_got_name(bot: Bot, event: MessageEvent, matcher: Matcher,
                              raw_arg=ArgPlainText("name")):
    matcher.state["name"] = raw_arg


@new_season_matcher.got("south_game_enabled", "是否开启半庄战？(y/n)")
async def new_season_got_east_game_enabled(bot: Bot, event: MessageEvent, matcher: Matcher,
                                           raw_arg=ArgPlainText("south_game_enabled")):
    if raw_arg == 'y':
        matcher.state["south_game_enabled"] = True
    else:
        matcher.state["south_game_enabled"] = False
        matcher.set_arg("south_game_horse_point", Message())


@new_season_matcher.got("south_game_horse_point", "半庄战马点？通过逗号分割")
@general_interceptor(new_season_matcher)
async def new_season_got_south_game_horse_point(bot: Bot, event: MessageEvent, matcher: Matcher,
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
async def new_season_got_east_game_enabled(bot: Bot, event: MessageEvent, matcher: Matcher,
                                           raw_arg=ArgPlainText("east_game_enabled")):
    if raw_arg == 'y':
        matcher.state["east_game_enabled"] = True
    else:
        matcher.state["east_game_enabled"] = False
        matcher.set_arg("east_game_horse_point", Message())

    if not matcher.state["south_game_enabled"] and not matcher.state["east_game_enabled"]:
        await matcher.finish("半庄战、东风战至少需要开启一种")


@new_season_matcher.got("east_game_horse_point", "东风战马点？通过空格分割")
@general_interceptor(new_season_matcher)
async def new_season_got_east_game_horse_point(bot: Bot, event: MessageEvent, matcher: Matcher,
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
@general_interceptor(new_season_matcher)
async def new_season_confirm(bot: Bot, event: MessageEvent, matcher: Matcher):
    season = SeasonOrm(code=matcher.state["code"],
                       name=matcher.state["name"],
                       south_game_enabled=matcher.state["south_game_enabled"],
                       south_game_horse_point=matcher.state["south_game_horse_point"],
                       east_game_enabled=matcher.state["east_game_enabled"],
                       east_game_horse_point=matcher.state["east_game_horse_point"])
    matcher.state["season"] = season

    with StringIO() as sio:
        map_season(sio, season, group_info=matcher.state["group_info"])
        sio.write("\n确定创建赛季吗？(y/n)")

        msg = sio.getvalue()

    await matcher.pause(msg)


@new_season_matcher.receive()
@general_interceptor(new_season_matcher)
async def new_season_handle(bot: Bot, event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        season = matcher.state["season"]
        season.group = await get_group_by_binding_qq(matcher.state["binding_qq"])
        season = await season_service.new_season(season)
        matcher.state["season_id"] = season.id
        await matcher.pause("赛季创建成功。是否立刻开启该赛季？(y/n)")
    else:
        await matcher.finish("取消赛季创建")


@new_season_matcher.receive()
@general_interceptor(new_season_matcher)
async def new_season_start(bot: Bot, event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        # 因为session不同，所以需要重新获取season
        season = await season_service.get_season_by_id(matcher.state["season_id"])
        await season_service.start_season(season)
        await matcher.finish("赛季开启成功")
    else:
        await matcher.finish("稍后可以使用“/开启赛季”命令开启赛季")
