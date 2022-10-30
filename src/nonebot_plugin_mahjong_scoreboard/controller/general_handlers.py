from typing import Type

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot, ActionFailed
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.context import get_context
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.utils import get_group_info, split_message, \
    parse_int_or_error
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq, ensure_group_admin
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq


def require_group_binding_qq(matcher_type: Type[Matcher], check_admin: bool = False):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def prepare(event: MessageEvent, matcher: Matcher):
        if isinstance(event, GroupMessageEvent):
            matcher.state["binding_qq"] = event.group_id

    require_integer(matcher_type, "binding_qq", "群号")

    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def handle(event: MessageEvent, matcher: Matcher):
        binding_qq = matcher.state["binding_qq"]
        matcher.state["group_info"] = await get_group_info(binding_qq)
        matcher.state["binding_qq"] = binding_qq

        if check_admin:
            group = await get_group_by_binding_qq(binding_qq)
            user = await get_user_by_binding_qq(event.user_id)

            await ensure_group_admin(user, group)

    return matcher_type


def require_user_binding_qq(matcher_type: Type[Matcher],
                            *, check_in_group: bool = True,
                            sender_as_default_on_group_msg: bool = True):
    if sender_as_default_on_group_msg:
        @matcher_type.handle()
        @general_interceptor(matcher_type)
        async def prepare(event: MessageEvent, matcher: Matcher):
            if isinstance(event, GroupMessageEvent):
                matcher.state.setdefault("user_binding_qq", event.user_id)

    require_integer(matcher_type, "user_binding_qq", "用户QQ号")

    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def handle(bot: Bot, matcher: Matcher):
        user_binding_qq = matcher.state["user_binding_qq"]

        if check_in_group:
            group_binding_qq = matcher.state.get("binding_qq")
            try:
                member_info = await bot.get_group_member_info(user_id=user_binding_qq, group_id=group_binding_qq)
                matcher.state["member_info"] = member_info
            except ActionFailed:
                raise BadRequestError("该成员不在群中")

    return matcher_type


def require_integer(matcher_type: Type[Matcher], arg_name: str, desc: str):
    @matcher_type.handle()
    async def check(matcher: Matcher):
        if arg_name not in matcher.state:
            await matcher.pause(desc + "？")

    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def receive(event: MessageEvent, matcher: Matcher):
        if arg_name not in matcher.state:
            arg = event.message.extract_plain_text()
            arg = parse_int_or_error(arg, desc)
            matcher.state[arg_name] = arg

    return matcher_type


def require_str(matcher_type: Type[Matcher], arg_name: str, desc: str):
    @matcher_type.handle()
    async def check(matcher: Matcher):
        if arg_name not in matcher.state:
            await matcher.pause(desc + "？")

    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def receive(event: MessageEvent, matcher: Matcher):
        if arg_name not in matcher.state:
            arg = event.message.extract_plain_text()
            matcher.state[arg_name] = arg

    return matcher_type


def require_parse_unary_text_arg(matcher_type: Type[Matcher], arg_name: str):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def parse_args(event: MessageEvent, matcher: Matcher):
        text = None

        args = split_message(event.message)[1:]
        for arg in args:
            if arg.type == "text":
                text = arg.data["text"]

        if text is not None:
            matcher.state[arg_name] = text

    return matcher_type


def require_parse_unary_integer_arg(matcher_type: Type[Matcher], arg_name: str):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def parse_args(event: MessageEvent, matcher: Matcher):
        text = None

        args = split_message(event.message)[1:]
        for arg in args:
            if arg.type == "text":
                text = arg.data["text"]

        if text is not None:
            matcher.state[arg_name] = parse_int_or_error(text, arg_name)

    return matcher_type


def require_parse_unary_at_arg(matcher_type: Type[Matcher], name: str):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def handle(event: MessageEvent, matcher: Matcher):
        args = split_message(event.message)
        if len(args) > 1 and args[1].type == 'at':
            matcher.state[name] = int(args[1].data["qq"])

    return matcher_type


def require_game_code_from_context(matcher_type: Type[Matcher]):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def prepare(event: MessageEvent, matcher: Matcher):
        context = get_context(event)
        if context and "game_code" in context:
            matcher.state["game_code"] = context["game_code"]

    return matcher_type
