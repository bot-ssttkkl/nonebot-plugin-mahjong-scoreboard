from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....model import RankPointPolicy


async def migrate_v3_to_v4():
    from ..data_source import data_source
    from ...data_model import SeasonOrm

    async with AsyncSession(data_source.engine) as sess:
        result = await sess.execute(select(SeasonOrm.id, SeasonOrm.config))
        for (id_, config) in result.all():
            config.rank_point_policy = RankPointPolicy.horse_point
            if config.south_game_enabled:
                config.south_game_initial_point = 25000
            if config.east_game_enabled:
                config.east_game_initial_point = 25000

            stmt = update(SeasonOrm).where(SeasonOrm.id == id_).values(config=config)
            await sess.execute(stmt)
        await sess.commit()
