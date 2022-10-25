from typing import Type

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText

from ml_hitwh.controller.interceptor import workflow_interceptor
from ml_hitwh.controller.utils import parse_int_or_reject, get_group_info
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service.group_service import get_group_by_binding_qq, is_group_admin
from ml_hitwh.service.user_service import get_user_by_binding_qq


def require_group_binding_qq(matcher_type: Type[Matcher], require_admin: bool = False):
    @matcher_type.handle()
    @workflow_interceptor(matcher_type)
    async def new_season_begin(event: MessageEvent, matcher: Matcher):
        if isinstance(event, GroupMessageEvent):
            matcher.set_arg("binding_qq", Message(str(event.group_id)))

    @matcher_type.got("binding_qq", "群号？")
    @workflow_interceptor(matcher_type)
    async def got(event: MessageEvent, matcher: Matcher,
                  raw_arg=ArgPlainText("binding_qq")):
        binding_qq = await parse_int_or_reject(raw_arg, "群号", matcher)

        matcher.state["group_info"] = await get_group_info(binding_qq)
        matcher.state["binding_qq"] = binding_qq

        if require_admin:
            group = await get_group_by_binding_qq(binding_qq)
            user = await get_user_by_binding_qq(event.user_id)

            if not await is_group_admin(user, group):
                raise BadRequestError("没有权限")

    return matcher_type
