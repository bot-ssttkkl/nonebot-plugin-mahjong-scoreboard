import asyncio

from nonebot import logger, Driver, get_driver
from nonebot.message import run_postprocessor
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_scoped_session
from sqlalchemy.orm import registry
from sqlalchemy.orm import sessionmaker

from ml_hitwh.config import conf

mapper_registry = registry()
OrmBase = mapper_registry.generate_base()


class DataSourceNotReadyError(RuntimeError):
    pass


class DataSource:
    def __init__(self, driver: Driver):
        self._engine = None
        self._session = None

        @driver.on_startup
        async def on_startup():
            self._engine = create_async_engine(conf.ml_database_conn_url,
                                               # 仅当debug模式时回显sql语句
                                               echo=driver.config.log_level == 'debug',
                                               future=True)
            # noinspection PyUnresolvedReferences
            from . import game, group, season, user

            async with self._engine.begin() as conn:
                await conn.run_sync(OrmBase.metadata.create_all)

            # expire_on_commit=False will prevent attributes from being expired
            # after commit.
            session_factory = sessionmaker(
                self._engine, expire_on_commit=False, class_=AsyncSession
            )
            self._session = async_scoped_session(session_factory, scopefunc=asyncio.current_task)
            logger.success("Succeeded to initialize data source")

        @driver.on_shutdown
        async def on_shutdown():
            await self._engine.dispose()

            self._engine = None
            self._session = None

            logger.success("Succeeded to dispose data source")

        run_postprocessor(self.remove_session)

    def session(self) -> AsyncSession:
        if self._session is None:
            raise DataSourceNotReadyError()
        return self._session()

    async def remove_session(self):
        if self._session is None:
            raise DataSourceNotReadyError()
        await self._session.remove()


data_source = DataSource(get_driver())

__all__ = ("DataSource", "data_source")
