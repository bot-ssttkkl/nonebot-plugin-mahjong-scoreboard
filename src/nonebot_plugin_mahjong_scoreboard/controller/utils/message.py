from typing import List, Optional

from nonebot.adapters.qqguild import Message, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot.params import CommandArg


def split_message(message: Message, ignore_empty: bool = True) -> List[MessageSegment]:
    result = []
    for seg in message:
        if seg.type == "text":
            for text in seg.data["text"].split(" "):
                if not ignore_empty or text:
                    result.append(MessageSegment.text(text))
        else:
            result.append(seg)

    return result

