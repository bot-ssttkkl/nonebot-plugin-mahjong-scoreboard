from typing import List

from nonebot.adapters.qqguild import Message, MessageSegment


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

