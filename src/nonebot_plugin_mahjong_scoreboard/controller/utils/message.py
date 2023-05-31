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


def SplitCommandArgs(*, lookup_matcher_state: bool = False,
                     lookup_matcher_state_key: Optional[str] = "command_args_store",
                     ignore_empty: bool = True):
    def dep(matcher: Matcher, command_arg=CommandArg()):
        if lookup_matcher_state:
            command_arg = matcher.state[lookup_matcher_state_key]
        return split_message(command_arg, ignore_empty)

    return Depends(dep)
