from io import StringIO

from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import MessageEvent, Message, GroupMessageEvent
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import workflow_interceptor
from ml_hitwh.controller.mapper.season_mapper import map_season
from ml_hitwh.controller.utils import parse_int_or_reject, split_message, get_group_info
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import season_service
from ml_hitwh.service.group_service import get_group_by_binding_qq

# ========== 赛季信息 ==========
query_running_season_matcher = on_command("赛季信息", aliases={"查询赛季", "赛季"}, priority=5)


@query_running_season_matcher.handle()
@workflow_interceptor(query_running_season_matcher)
async def query_running_season_begin(bot: Bot, event: MessageEvent, matcher: Matcher):
    if isinstance(event, GroupMessageEvent):
        matcher.set_arg("binding_qq", Message(str(event.group_id)))

    args = split_message(event.message)
    if len(args) > 1 and args[1].type == 'text':
        matcher.state["season_code"] = args[1].data["text"]


@query_running_season_matcher.got("binding_qq", "群号？")
@workflow_interceptor(query_running_season_matcher)
async def query_running_season_got_group_binding_qq(event: MessageEvent, matcher: Matcher,
                                                    raw_arg=ArgPlainText("binding_qq")):
    binding_qq = await parse_int_or_reject(raw_arg, "群号", matcher)

    matcher.state["group_info"] = await get_group_info(binding_qq)
    matcher.state["binding_qq"] = binding_qq


@query_running_season_matcher.handle()
@workflow_interceptor(query_running_season_matcher)
async def query_running_season_handle(bot: Bot, event: MessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])

    season_code = matcher.state.get("season_code", None)
    if season_code:
        season = await season_service.get_season_by_code(season_code, group)
        if season is None:
            raise BadRequestError("找不到赛季")
    else:
        if group.running_season_id:
            season = await season_service.get_season_by_id(group.running_season_id)
        else:
            raise BadRequestError("当前没有运行中的赛季")

    with StringIO() as sio:
        map_season(sio, season, group_info=matcher.state["group_info"])
        msg = sio.getvalue()

    await matcher.send(msg)
