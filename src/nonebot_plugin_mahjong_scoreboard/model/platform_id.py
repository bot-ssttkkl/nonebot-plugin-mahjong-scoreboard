from typing import Optional, NamedTuple

from nonebot_plugin_session import Session, SessionIdType


class PlatformId(NamedTuple):
    platform: str
    bot_type: str
    real_id: str

    def __str__(self):
        return "_".join(self)

    @classmethod
    def parse(cls, value: str) -> "PlatformId":
        return PlatformId(*value.split("_", maxsplit=2))


def get_platform_user_id(session: Session) -> PlatformId:
    return PlatformId.parse(session.get_id(SessionIdType.USER, include_bot_id=False))


def get_platform_group_id(session: Session) -> Optional[PlatformId]:
    # 如果消息来自私聊，则session.get_id(SessionIdType.GROUP)返回的结果与session.get_id(SessionIdType.USER)相同
    res = PlatformId.parse(session.get_id(SessionIdType.GROUP, include_bot_id=False))
    platform_user_id = get_platform_user_id(session)
    if res != platform_user_id:
        return res
    else:
        return None
