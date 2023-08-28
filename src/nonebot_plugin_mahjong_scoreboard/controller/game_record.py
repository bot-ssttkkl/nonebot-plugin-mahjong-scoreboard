import re
from io import StringIO
from typing import Optional, NamedTuple

from cachetools import TTLCache
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot_plugin_session import Session

from .interceptor import handle_error
from .mapper.game_mapper import map_game
from .mg import matcher_group
from .utils.dep import GroupDep, UserDep, UnaryArg, SessionDep, SplitCommandArgs, SenderUserDep
from .utils.parse import parse_int_or_error, try_parse_wind, parse_float_or_error, try_parse_game_code
from ..errors import BadRequestError
from ..model import Group, User, PlayerAndWind, GameState, Wind
from ..service import game_service
from ..utils.nonebot import default_cmd_start
from ..model.identity import get_platform_group_id

group_latest_game_code = TTLCache[str, int](4096, 7200)


def GameCodeFromGroupLatest():
    def dependency(session=SessionDep()):
        platform_group_id = get_platform_group_id(session)
        if platform_group_id in group_latest_game_code:
            return group_latest_game_code[platform_group_id]

    return Depends(dependency)


# =============== 新建对局 ===============
new_game_matcher = matcher_group.on_command("新建对局", aliases={"新对局"}, priority=5)
new_game_matcher.__help_info__ = f"{default_cmd_start}新建对局 [四人南|四人东]"


@new_game_matcher.handle()
@handle_error()
async def new_game(matcher: Matcher, player_and_wind=UnaryArg(), session: Session = SessionDep(),
                   group=GroupDep(), promoter=SenderUserDep()):
    if player_and_wind == "四人东":
        player_and_wind = PlayerAndWind.four_men_east
    elif player_and_wind == "四人南":
        player_and_wind = PlayerAndWind.four_men_south
    elif player_and_wind:
        raise BadRequestError("对局类型不合法")

    game = await game_service.new_game(promoter.id, group.id, player_and_wind)

    msg = await map_game(game)
    msg += f'\n\n新建对局成功，对此消息回复“{default_cmd_start}结算 <成绩>”指令记录你的成绩'
    await matcher.send(msg)

    group_latest_game_code[get_platform_group_id(session)] = game.code


# =============== 结算 ===============
record_matcher = matcher_group.on_command("结算对局", aliases={"结算"}, priority=5)
record_matcher.__help_info__ = f"{default_cmd_start}结算对局 <成绩> [对局<编号>] [@<用户>] [<自风>]"


class RecordArgs(NamedTuple):
    game_code: int
    score: int
    wind: Optional[Wind]


@handle_error()
async def parse_record_args(args=SplitCommandArgs(), game_code=GameCodeFromGroupLatest()):
    score = None
    wind = None

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text.removeprefix("对局"), "对局编号")
            elif text.endswith("风"):
                wind = try_parse_wind(text[:len("风")])
            elif text.endswith("家"):
                wind = try_parse_wind(text[:len("家")])
            else:
                pending_wind = try_parse_wind(text)
                if pending_wind is not None:
                    wind = pending_wind
                else:
                    score = text

    score = parse_int_or_error(score, '成绩')

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    return RecordArgs(game_code, score, wind)


@record_matcher.handle()
@handle_error()
async def record(matcher: Matcher,
                 group: Group = GroupDep(),
                 user: User = UserDep(),
                 operator: User = SenderUserDep(),
                 args=Depends(parse_record_args)):
    game = await game_service.record_game(args.game_code, group.id, user.id,
                                          args.score, args.wind, operator.id)

    msg = await map_game(game)
    msg += '\n\n结算成功'
    if game.state == GameState.invalid_total_point:
        msg += f"\n警告：对局的成绩之和不正确，对此消息回复“{default_cmd_start}结算 <成绩>”指令重新记录你的成绩"
    await matcher.send(msg)


# =============== 撤销结算 ===============
revert_record_matcher = matcher_group.on_command("撤销结算对局", aliases={"撤销结算"}, priority=5)
revert_record_matcher.__help_info__ = f"{default_cmd_start}撤销结算对局 [对局<编号>] [@<用户>]"


@revert_record_matcher.handle()
@handle_error()
async def revert_record(matcher: Matcher,
                        group: Group = GroupDep(),
                        user: User = UserDep(),
                        operator: User = SenderUserDep(),
                        latest_game_code=GameCodeFromGroupLatest(),
                        game_code=UnaryArg(parser=try_parse_game_code)):
    if game_code is None:
        game_code = latest_game_code

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    game = await game_service.revert_record(game_code, group.id, user.id, operator.id)

    msg = await map_game(game)
    msg += '\n\n撤销结算成功'
    await matcher.send(msg)


# =============== 设置对局PT ===============
set_record_point_matcher = matcher_group.on_command("设置对局PT", aliases={"对局PT"}, priority=5)
set_record_point_matcher.__help_info__ = f"{default_cmd_start}设置对局PT <PT> [对局<编号>] [@<用户>]"


class SetRecordPointArgs(NamedTuple):
    game_code: int
    point: float


@handle_error()
async def parse_set_record_point_args(args=SplitCommandArgs(),
                                      game_code=GameCodeFromGroupLatest()):
    point = None

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text.removeprefix("对局"), "对局编号")
            else:
                point = text

    point = parse_float_or_error(point, 'PT')

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    return SetRecordPointArgs(game_code, point)


@set_record_point_matcher.handle()
@handle_error()
async def set_record_point(matcher: Matcher,
                           group: Group = GroupDep(),
                           user: User = UserDep(),
                           operator: User = SenderUserDep(),
                           args: SetRecordPointArgs = Depends(parse_set_record_point_args)):
    game = await game_service.set_record_point(args.game_code, group.id, user.id,
                                               args.point, operator.id)

    msg = await map_game(game)
    msg += '\n\n设置PT成功'
    await matcher.send(msg)


# =============== 删除对局 ===============
delete_game_matcher = matcher_group.on_command("删除对局", priority=5)
delete_game_matcher.__help_info__ = f"{default_cmd_start}删除对局 [对局<编号>]"


@delete_game_matcher.handle()
@handle_error()
async def delete_game(matcher: Matcher, group: Group = GroupDep(), operator: User = SenderUserDep(),
                      game_code=UnaryArg(parser=try_parse_game_code)):
    if game_code is None:
        raise BadRequestError("请指定对局编号")

    await game_service.delete_game(game_code, group.id, operator.id)

    await matcher.send(f'成功删除对局{game_code}')


# =============== 设置对局进度 ===============
make_game_progress_matcher = matcher_group.on_command("设置对局进度", aliases={"对局进度"}, priority=5)
make_game_progress_matcher.__help_info__ = f"{default_cmd_start}设置对局进度 <东/南x局y本场 或 完成> [对局<编号>]"

round_honba_pattern = r"([东南])([一二三四1234])局([0123456789零一两二三四五六七八九十百千万亿]+)本场"


class MakeGameProgressArgs(NamedTuple):
    game_code: int
    completed: bool
    round: Optional[int]
    honba: Optional[int]


@handle_error()
async def parse_make_game_progress_args(args=SplitCommandArgs(),
                                        game_code=GameCodeFromGroupLatest()):
    completed = False
    round = None
    honba = None

    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text.removeprefix("对局"), "对局编号")
            elif text == '完成' or text == '已完成':
                completed = True
            else:
                match_result = re.match(round_honba_pattern, text)
                if match_result is not None:
                    wind, round, honba = match_result.groups()

                    round = parse_int_or_error(round, "局数", True)
                    if wind == '南':
                        round += 4

                    honba = parse_int_or_error(honba, "本场", True)

    if game_code is None:
        raise BadRequestError("请指定对局编号")
    if not completed and (round is None or honba is None):
        raise BadRequestError("请指定对局进度（”东/南x局y本场“或”完成“）")

    return MakeGameProgressArgs(game_code, completed, round, honba)


@make_game_progress_matcher.handle()
@handle_error()
async def make_game_progress(matcher: Matcher, group: Group = GroupDep(), operator: User = SenderUserDep(),
                             args: MakeGameProgressArgs = Depends(parse_make_game_progress_args)):
    if not args.completed:
        game = await game_service.make_game_progress(args.game_code,
                                                     args.round,
                                                     args.honba,
                                                     group.id, operator.id)
    else:
        game = await game_service.remove_game_progress(args.game_code, group.id)

    msg = await map_game(game)
    msg += "\n\n成功设置对局进度"
    await matcher.send(msg)


# ========== 设置对局备注 ===========
set_game_comment_matcher = matcher_group.on_command("设置对局备注", aliases={"对局备注"}, priority=5)
set_game_comment_matcher.__help_info__ = f"{default_cmd_start}设置对局备注 [对局<编号>] <备注文本>"


class SetGameCommentArgs(NamedTuple):
    game_code: int
    comment: str


@handle_error()
async def parse_set_game_comment_args(args=SplitCommandArgs(ignore_empty=False),
                                      game_code=GameCodeFromGroupLatest()):
    comment = StringIO()

    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if game_code is None and text.startswith("对局"):
                game_code = parse_int_or_error(text.removeprefix("对局"), "对局编号")
            else:
                comment.write(text)
                comment.write(" ")

    comment = comment.getvalue()
    if not comment:
        raise BadRequestError("请输入备注")

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    return SetGameCommentArgs(game_code, comment)


@set_game_comment_matcher.handle()
@handle_error()
async def set_game_comment(matcher: Matcher, group: Group = GroupDep(), operator: User = SenderUserDep(),
                           args: SetGameCommentArgs = Depends(parse_set_game_comment_args)):
    game = await game_service.set_game_comment(args.game_code, group.id, args.comment,
                                               operator.id)

    msg = await map_game(game)
    msg += "\n\n成功设置对局备注"
    await matcher.send(msg)
