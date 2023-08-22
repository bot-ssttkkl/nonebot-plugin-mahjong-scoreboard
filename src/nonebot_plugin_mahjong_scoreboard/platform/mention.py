from typing import Optional

from nonebot.internal.adapter import MessageSegment

from nonebot_plugin_mahjong_scoreboard.model.platform_id import PlatformId

try:
    from nonebot.adapters.qqguild import MessageSegment as QQGuildMessageSegment
except ImportError:
    QQGuildMessageSegment = None

try:
    from nonebot.adapters.onebot.v11 import MessageSegment as OneBotV11MessageSegment
except ImportError:
    OneBotV11MessageSegment = None


def extract_mention_user(seg: MessageSegment) -> Optional[PlatformId]:
    if isinstance(seg, QQGuildMessageSegment):
        if seg.type == 'mention_user':
            return PlatformId("qqguild", "QQ Guild", seg.data['user_id'])
    elif isinstance(seg, OneBotV11MessageSegment):
        if seg.type == 'at':
            return PlatformId("qq", "OneBot V11", seg.data['qq'])

    return None
