from typing import TextIO

from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonUserPointOrm, SeasonOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import get_user_nickname


async def map_season_user_point(io: TextIO, sup: SeasonUserPointOrm, rank: int, total: int):
    session = data_source.session()

    user = await session.get(UserOrm, sup.user_id)
    season = await session.get(SeasonOrm, sup.season_id)
    group = await session.get(GroupOrm, season.group_id)

    name = await get_user_nickname(user, group)

    # [用户名]在赛季[赛季名]
    # PT：+114
    io.write(name)
    io.write("在赛季")
    io.write(season.name)
    io.write('\n')

    io.write("PT：")
    if sup.point > 0:
        io.write('+')
    elif sup.point == 0:
        io.write('±')
    io.write(str(sup.point))

    # 位次：+114
    io.write('\n位次：')
    io.write(str(rank))
    io.write('/')
    io.write(str(total))
