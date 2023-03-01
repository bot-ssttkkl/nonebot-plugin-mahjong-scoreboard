from typing import List, Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent
from nonebot.internal.params import Depends
from nonebot.params import CommandArg


def get_reply_message_id(event: MessageEvent) -> Optional[int]:
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break
    return message_id


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


def SplitCommandArgs(ignore_empty: bool = True):
    def dep(raw_args=CommandArg()):
        return split_message(raw_args, ignore_empty)

    return Depends(dep)
