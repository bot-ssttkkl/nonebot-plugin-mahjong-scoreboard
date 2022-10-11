from nonebot import get_driver
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker, registry

from ml_hitwh.config import conf

driver = get_driver()

mapper_registry = registry()
OrmBase = mapper_registry.generate_base()

sql_engine: AsyncEngine = None
SQLSession: sessionmaker = None


@driver.on_startup
async def on_startup():
    global sql_engine, SQLSession
    sql_engine = create_async_engine(conf.ml_database_conn_url,
                                     # 仅当debug模式时回显sql语句
                                     echo=driver.config.log_level == 'debug',
                                     future=True)

    from . import game, group, season, user

    async with sql_engine.begin() as conn:
        await conn.run_sync(OrmBase.metadata.create_all)

    SQLSession = sessionmaker(
        sql_engine, expire_on_commit=False, class_=AsyncSession
    )


@driver.on_shutdown
async def on_shutdown():
    global sql_engine, SQLSession

    await sql_engine.dispose()

    sql_engine = None
    SQLSession = None
