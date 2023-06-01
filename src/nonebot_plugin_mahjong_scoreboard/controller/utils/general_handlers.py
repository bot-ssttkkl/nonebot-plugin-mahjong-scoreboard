from typing import Type, Optional, Callable

from nonebot.internal.adapter import Event
from nonebot.internal.matcher import current_matcher, Matcher, current_bot, current_event
from nonebot.params import CommandArg
from nonebot_plugin_session import Session, extract_session

from .dep import SessionDep, MentionUserArg
from ..interceptor import handle_error, handle_interruption
from ...utils.session import get_platform_group_id, get_platform_user_id


async def hint_for_question_flow_on_first():
    matcher = current_matcher.get()
    if not matcher.state.get("hinted_for_question_flow", False):
        await matcher.send("进入问答模式，回复”/q“中止流程")
        matcher.state["hinted_for_question_flow"] = True


def require_store_command_args(matcher_type: Type[Matcher], dest: str = "command_args_store"):
    """
    将当前消息的command_args保存至matcher.state[dest]，配合require_arg使用
    """

    @matcher_type.handle()
    @handle_error()
    async def store_command_args(matcher: Matcher, command_args=CommandArg()):
        matcher.state[dest] = command_args


def require_arg(matcher_type: Type[Matcher], dest: str, desc: str,
                *, parser: Optional[Callable[[str], any]] = None):
    """
    若matcher.state[dest]不存在，则向用户询问并保存到matcher.state[dest]
    """

    @matcher_type.handle()
    @handle_error()
    async def check(matcher: Matcher):
        if dest not in matcher.state:
            await hint_for_question_flow_on_first()
            await matcher.pause(desc + "？")

    @matcher_type.handle()
    @handle_interruption()
    @handle_error()
    async def receive(event: Event, matcher: Matcher):
        if dest not in matcher.state:
            arg = event.get_message().extract_plain_text()
            if parser is not None:
                arg = parser(arg)
            matcher.state[dest] = arg

    return matcher_type


def _parse_platform_id(raw_id: str) -> str:
    # 实际上QQ频道不会调用到这里
    session = extract_session(current_bot.get(), current_event.get())
    return f"{session.platform}_{session.bot_type}_{raw_id}"


def require_platform_group_id(matcher_type: Type[Matcher], *, dest: str = "platform_group_id"):
    """
    私聊环境下向用户询问群号，群聊环境下则直接使用本群群号。保存到matcher.state[dest]
    """

    @matcher_type.handle()
    @handle_error()
    async def prepare(matcher: Matcher, session: Session = SessionDep()):
        platform_group_id = get_platform_group_id(session)
        if platform_group_id is not None:
            matcher.state[dest] = platform_group_id

    require_arg(matcher_type, dest, "群组ID", parser=_parse_platform_id)

    return matcher_type


def require_platform_user_id(matcher_type: Type[Matcher], *, dest: str = "platform_user_id",
                             lookup_matcher_state: bool = True,
                             lookup_matcher_state_key: Optional[str] = "command_args_store",
                             use_sender_on_group_message: bool = True,
                             ask_on_group_message: bool = False):
    """
    私聊环境下向用户询问用户号，群聊环境下则使用消息中的艾特或是发送者。保存到matcher.state[dest]
    """

    @matcher_type.handle()
    @handle_error()
    async def prepare(matcher: Matcher, session: Session = SessionDep(),
                      mention_user_id=MentionUserArg(lookup_matcher_state=lookup_matcher_state,
                                                     lookup_matcher_state_key=lookup_matcher_state_key)):
        platform_user_id = None
        if lookup_matcher_state_key is not None:
            platform_user_id = mention_user_id

        if use_sender_on_group_message:
            platform_group_id = get_platform_group_id(session)
            if platform_group_id is not None:  # 群聊环境
                platform_user_id = get_platform_user_id(session)

        if platform_user_id is not None:
            matcher.state[dest] = platform_user_id

    if ask_on_group_message:
        require_arg(matcher_type, dest, "用户ID", parser=_parse_platform_id)

    return matcher_type
