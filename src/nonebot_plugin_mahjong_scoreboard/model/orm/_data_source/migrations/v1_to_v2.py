from sqlalchemy import text

from ..src import data_source


async def migrate_v1_to_v2():
    async with data_source.engine.begin() as conn:
        await conn.execute(text("ALTER TABLE game_records ADD point_scale integer NOT NULL DEFAULT 0;"))
