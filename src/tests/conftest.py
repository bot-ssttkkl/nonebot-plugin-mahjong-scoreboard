import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    # 加载插件
    nonebot.load_plugin("nonebot_plugin_mahjong_scoreboard")
