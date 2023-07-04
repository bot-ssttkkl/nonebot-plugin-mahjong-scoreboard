from injector import Module, singleton, provider
from nonebot import get_driver
from pydantic import BaseSettings

from nonebot_plugin_mahjong_scoreboard.inj import add_module


class Config(BaseSettings):
    mahjong_scoreboard_api_baseurl: str = "http://localhost:8000"
    mahjong_scoreboard_api_secret: str = "secret"
    mahjong_scoreboard_send_forward_message: bool = True

    class Config:
        extra = "ignore"


@add_module
class ConfigModule(Module):
    @singleton
    @provider
    def provide_config(self) -> Config:
        return Config(**get_driver().config.dict())
