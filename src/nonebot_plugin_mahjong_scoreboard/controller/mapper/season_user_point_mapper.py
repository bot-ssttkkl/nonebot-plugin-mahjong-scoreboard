from io import StringIO

from nonebot.internal.matcher import current_bot

from . import map_point
from ...model import SeasonUserPoint, Season
from ...utils.nickname import get_user_nickname


async def map_season_user_point(sup: SeasonUserPoint, season: Season) -> str:
    bot = current_bot.get()
    with StringIO() as io:
        # [用户名]在赛季[赛季名]
        # PT：+114
        # 位次：30/36
        io.write(
            f"[{await get_user_nickname(bot, sup.user.platform_user_id, season.group.platform_group_id)}]"
            f"在赛季[{season.name}]\n")
        io.write(f"PT：{map_point(sup.point, season.config.point_precision)}\n")

        if sup.rank is not None:
            # 位次：+114
            io.write(f'位次：{sup.rank}')
            if sup.total is not None:
                io.write(f'/{sup.total}')

        return io.getvalue().strip()
