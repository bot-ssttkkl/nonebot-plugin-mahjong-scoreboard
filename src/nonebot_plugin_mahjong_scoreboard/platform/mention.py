from typing import Optional

from nonebot_plugin_mahjong_scoreboard.model.platform_id import PlatformId
from nonebot_plugin_mahjong_scoreboard.platform.func_registry import func

try:
    from nonebot.adapters.qqguild import Adapter as QQGuildAdapter
    from nonebot.adapters.qqguild import MessageSegment as QQGuildMessageSegment


    @func.register(QQGuildAdapter.get_name(), "extract_mention_user")
    def extract_mention_user(seg: QQGuildMessageSegment) -> Optional[PlatformId]:
        if seg.type == 'mention_user':
            return PlatformId("qqguild", "QQ Guild", seg.data['user_id'])

        return None

except ImportError:
    pass

try:
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
    from nonebot.adapters.onebot.v11 import MessageSegment as OneBotV11MessageSegment


    @func.register(OneBotV11Adapter.get_name(), "extract_mention_user")
    def extract_mention_user(seg: OneBotV11MessageSegment) -> Optional[PlatformId]:
        if seg.type == 'at':
            return PlatformId("qq", "OneBot V11", seg.data['qq'])

        return None

except ImportError:
    pass
