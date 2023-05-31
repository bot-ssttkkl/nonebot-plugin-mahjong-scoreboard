from typing import Optional

from nonebot.internal.adapter import MessageSegment

try:
    from nonebot.adapters.qqguild import MessageSegment as QQGuildMessageSegment
except ImportError:
    QQGuildMessageSegment = None

try:
    from nonebot.adapters.onebot.v11 import MessageSegment as OneBotV11MessageSegment
except ImportError:
    OneBotV11MessageSegment = None


def extract_mention_user(seg: MessageSegment) -> Optional[str]:
    if isinstance(seg, QQGuildMessageSegment):
        if seg.type == 'mention_user':
            return f"qqguild_QQ Guild_{seg.data['user_id']}"
    elif isinstance(seg, OneBotV11MessageSegment):
        if seg.type == 'at':
            return f"qq_OneBot V11_{seg.data['qq']}"

    return None
