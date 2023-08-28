from typing import Optional, Union

from nonebot.internal.matcher import current_matcher

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model import Wind
from nonebot_plugin_mahjong_scoreboard.utils.integer import decode_integer


def parse_int_or_error(raw: Union[int, str, None],
                       desc: str,
                       allow_chinese: bool = False,
                       max: Optional[int] = None,
                       min: Optional[int] = None) -> int:
    if not raw:
        raise BadRequestError(f"请指定{desc}")

    try:
        if allow_chinese:
            x = decode_integer(raw)
        else:
            x = int(raw)

        if max is not None and x > max or min is not None and x < min:
            raise ValueError(x)

        return x
    except ValueError:
        comment = [f"输入的{desc}不合法", f"输入值：{raw}"]
        if min is not None:
            comment.append(f"最小值：{min}")
        if max is not None:
            comment.append(f"最大值：{max}")
        comment = '，'.join(comment)
        if len(comment) != 0:
            comment = f"（{comment}）"
        raise BadRequestError(comment)


async def parse_int_or_reject(raw: Union[int, str, None],
                              desc: str,
                              allow_chinese: bool = False,
                              max: Optional[int] = None,
                              min: Optional[int] = None) -> int:
    matcher = current_matcher.get()
    try:
        return parse_int_or_error(raw, desc, allow_chinese, max, min)
    except BadRequestError as e:
        await matcher.reject(e.message)


def parse_float_or_error(raw: Union[float, int, str, None], desc: str) -> float:
    if not raw:
        raise BadRequestError(f"请指定{desc}")

    try:
        return float(raw)
    except ValueError:
        raise BadRequestError(f"输入的{desc}不合法，输入值：{raw}")


async def parse_float_or_reject(raw: Union[float, int, str, None], desc: str) -> float:
    matcher = current_matcher.get()

    try:
        return parse_float_or_error(raw, desc)
    except BadRequestError as e:
        await matcher.reject(e.message)


def try_parse_wind(text: str) -> Optional[Wind]:
    if text == "东":
        return Wind.east
    if text == "南":
        return Wind.south
    if text == "西":
        return Wind.west
    if text == "北":
        return Wind.north
    return None


def try_parse_game_code(text: str) -> Optional[int]:
    if text.startswith("对局"):
        return parse_int_or_error(text.removeprefix("对局"), "对局编号")
    return None
