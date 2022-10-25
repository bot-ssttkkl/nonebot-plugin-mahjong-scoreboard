from typing import List, Optional, Union

from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent, ActionFailed
from nonebot.internal.matcher import Matcher, current_bot

from ml_hitwh.errors import BadRequestError


def get_reply_message_id(event: MessageEvent) -> Optional[int]:
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break
    return message_id


def split_message(message: Message) -> List[MessageSegment]:
    result = []
    for seg in message:
        if seg.type == "text":
            for text in seg.data["text"].split(" "):
                if text:
                    result.append(MessageSegment.text(text))
        else:
            result.append(seg)

    return result


async def get_group_info(group_binding_qq: int):
    bot = current_bot.get()
    try:
        group_info = await bot.get_group_info(group_id=group_binding_qq)
        # 如果机器人尚未加入群, group_create_time, group_level, max_member_count 和 member_count 将会为0
        if group_info["member_count"] == 0:
            raise BadRequestError("机器人尚未加入群")
        return group_info
    except ActionFailed as e:
        raise BadRequestError(e.info["wording"])


def parse_int_or_error(raw: Union[int, str, None], desc: str) -> int:
    if not raw:
        raise BadRequestError(f"请指定{desc}")

    try:
        return int(raw)
    except ValueError:
        raise BadRequestError(f"输入的{desc}不合法")


async def parse_int_or_reject(raw: Union[int, str, None], desc: str, matcher: Matcher) -> int:
    if not raw:
        await matcher.reject(f"请指定{desc}")

    try:
        return int(raw)
    except ValueError:
        await matcher.reject(f"输入的{desc}不合法。请重新输入")


async def parse_int_or_finish(raw: Union[int, str, None], desc: str, matcher: Matcher) -> int:
    if not raw:
        await matcher.finish(f"请指定{desc}")

    try:
        return int(raw)
    except ValueError:
        await matcher.finish(f"输入的{desc}不合法")
