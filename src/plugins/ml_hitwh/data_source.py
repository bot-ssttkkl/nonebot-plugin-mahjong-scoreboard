from beanie import init_beanie
from bson import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient
from nonebot import get_driver

from ml_hitwh.config import conf
from ml_hitwh.model import DOC_MODELS

_client = None
_db = None


@get_driver().on_startup
async def _init():
    global _client, _db
    _client = AsyncIOMotorClient(conf.ml_mongo_conn_url)
    _db = _client[conf.ml_mongo_database_name].with_options(
        CodecOptions(tz_aware=True)
    )

    await init_beanie(database=_db, document_models=DOC_MODELS)


@get_driver().on_shutdown
def _destroy():
    global _client, _db
    if _client is not None:
        # noinspection PyUnresolvedReferences
        _client.close()
    _client = None
    _db = None


def db():
    return _db
