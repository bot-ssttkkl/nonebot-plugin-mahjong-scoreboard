from sqlalchemy import Column, String, JSON, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from .src import data_source

APP_DB_VERSION = 2


@data_source.registry.mapped
class MetaInfoOrm:
    __tablename__ = 'metainfo'

    key: str = Column(String(64), primary_key=True)
    value = Column(JSON)


async def get_metainfo(key: str):
    async with AsyncSession(data_source.engine) as session:
        record = await session.get(MetaInfoOrm, key)
        return record.value


async def set_metainfo(key: str, value: any):
    async with AsyncSession(data_source.engine) as session:
        record = await session.get(MetaInfoOrm, key)
        if record is None:
            record = MetaInfoOrm(key=key, value=value)
            session.add(record)

        record.value = value
        await session.commit()


@data_source.on_engine_created
async def initialize_metainfo():
    async with data_source.engine.begin() as conn:
        await conn.run_sync(lambda conn: MetaInfoOrm.__table__.create(conn, checkfirst=True))

    async with data_source.engine.begin() as conn:
        async with AsyncSession(data_source.engine, expire_on_commit=False) as session:
            # 判断是否初次建库
            blank_database = not await conn.run_sync(lambda conn: inspect(conn).has_table("games"))
            if blank_database:
                result = MetaInfoOrm(key="db_version", value=APP_DB_VERSION)
                session.add(result)
                await session.commit()
            else:
                stmt = select(MetaInfoOrm).where(MetaInfoOrm.key == "db_version")
                result = (await session.execute(stmt)).scalar_one_or_none()
                if result is None:
                    result = MetaInfoOrm(key="db_version", value=1)
                    session.add(result)
                    await session.commit()

        await conn.commit()
