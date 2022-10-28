from typing import Type

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import workflow_interceptor
from ml_hitwh.controller.utils import parse_int_or_reject, get_group_info, split_message
from ml_hitwh.service.group_service import get_group_by_binding_qq, ensure_group_admin
from ml_hitwh.service.user_service import get_user_by_binding_qq


def require_group_binding_qq(matcher_type: Type[Matcher], check_admin: bool = False):
    @matcher_type.handle()
    @workflow_interceptor(matcher_type)
    async def handle(event: MessageEvent, matcher: Matcher):
        if isinstance(event, GroupMessageEvent):
            matcher.set_arg("binding_qq", Message(str(event.group_id)))

    @matcher_type.got("binding_qq", "群号？")
    @workflow_interceptor(matcher_type)
    async def got(event: MessageEvent, matcher: Matcher,
                  raw_arg=ArgPlainText("binding_qq")):
        binding_qq = await parse_int_or_reject(raw_arg, "群号")

        matcher.state["group_info"] = await get_group_info(binding_qq)
        matcher.state["binding_qq"] = binding_qq

        if check_admin:
            group = await get_group_by_binding_qq(binding_qq)
            user = await get_user_by_binding_qq(event.user_id)

            await ensure_group_admin(user, group)

    return matcher_type


def require_unary_text(matcher_type: Type[Matcher], name: str, *, decorator=None):
    async def handle(event: MessageEvent, matcher: Matcher):
        args = split_message(event.message)
        if len(args) > 1 and args[1].type == 'text':
            matcher.state[name] = args[1].data["text"]

    if decorator:
        handle = decorator(handle)

    matcher_type.append_handler(handle)
    return matcher_type


def require_unary_at(matcher_type: Type[Matcher], name: str, *, decorator=None):
    async def handle(event: MessageEvent, matcher: Matcher):
        args = split_message(event.message)
        if len(args) > 1 and args[1].type == 'at':
            matcher.state[name] = int(args[1].data["qq"])

    if decorator:
        handle = decorator(handle)

    matcher_type.append_handler(handle)
    return matcher_type
