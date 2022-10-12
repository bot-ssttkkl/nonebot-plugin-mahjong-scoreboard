from io import StringIO

from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message, ActionFailed
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.season_mapper import map_season
from ml_hitwh.controller.utils import parse_int_or_reject
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import season_service

start_season_matcher = on_command("开启赛季", priority=5)


@start_season_matcher.handle()
@general_interceptor(start_season_matcher)
async def start_season_begin(bot: Bot, event: MessageEvent, matcher: Matcher):
    if isinstance(event, GroupMessageEvent):
        matcher.set_arg("binding_qq", Message(str(event.group_id)))


@start_season_matcher.got("binding_qq", "群号？")
@general_interceptor(start_season_matcher)
async def start_season_got_group_binding_qq(bot: Bot, event: MessageEvent, matcher: Matcher,
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


@start_season_matcher.got("code", "赛季代号？")
@general_interceptor(start_season_matcher)
async def start_season_matcher_got_code(bot: Bot, event: MessageEvent, matcher: Matcher,
                                        raw_arg=ArgPlainText("code")):
    season = await season_service.get_season_by_code(raw_arg, matcher.state["group"])
    if season is None:
        await matcher.finish("找不到赛季。使用“/新赛季”指令创建赛季")

    matcher.state["season"] = season
    matcher.state["season_id"] = season.id


@start_season_matcher.handle()
@general_interceptor(start_season_matcher)
async def new_season_confirm(bot: Bot, event: MessageEvent, matcher: Matcher):
    season = matcher.state["season"]

    with StringIO() as sio:
        map_season(sio, season, group_info=matcher.state["group_info"])
        sio.write("\n确定开启赛季吗？(y/n)")

        msg = sio.getvalue()

    await matcher.pause(msg)


@start_season_matcher.receive()
@general_interceptor(start_season_matcher)
async def new_season_end(bot: Bot, event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        # 因为session不同，所以需要重新获取season
        season = await season_service.get_season_by_id(matcher.state["season_id"])
        await season_service.start_season(season)
        await matcher.finish("赛季开启成功")
    else:
        await matcher.finish("取消赛季开启")
