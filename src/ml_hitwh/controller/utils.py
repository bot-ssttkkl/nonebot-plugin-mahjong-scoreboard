from typing import List, Optional, Union

from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent
from nonebot.internal.matcher import Matcher

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
