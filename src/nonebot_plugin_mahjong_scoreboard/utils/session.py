from typing import Optional

from nonebot_plugin_session import Session, SessionIdType


def get_platform_user_id(session: Session) -> str:
    return session.get_id(SessionIdType.USER, include_bot_id=False)


def get_platform_group_id(session: Session) -> Optional[str]:
    # 如果消息来自私聊，则session.get_id(SessionIdType.GROUP)返回的结果与session.get_id(SessionIdType.USER)相同
    res = session.get_id(SessionIdType.GROUP, include_bot_id=False)
    platform_user_id = get_platform_user_id(session)
    if res != platform_user_id:
        return res
    else:
        return None


def get_real_id(platform_id: str) -> str:
    platform, bot_type, real_id = platform_id.split("_", maxsplit=2)
    return real_id
