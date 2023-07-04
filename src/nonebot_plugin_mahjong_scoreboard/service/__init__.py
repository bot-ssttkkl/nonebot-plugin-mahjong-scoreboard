from httpx import AsyncClient
from injector import Module, singleton, provider
from nonebot import logger, get_driver

from nonebot_plugin_mahjong_scoreboard import Config
from nonebot_plugin_mahjong_scoreboard.inj import add_module


@add_module
class ClientModule(Module):
    @singleton
    @provider
    def provide_async_client(self, conf: Config) -> AsyncClient:
        async def req_hook(request):
            logger.trace(f"Request: {request.method} {request.url} - Waiting for response")

        async def resp_hook(response):
            request = response.request
            logger.trace(f"Response: {request.method} {request.url} - Status {response.status_code}")
            response.raise_for_status()

        client = AsyncClient(
            base_url=conf.mahjong_scoreboard_api_baseurl,
            follow_redirects=True,
            event_hooks={'request': [req_hook], 'response': [resp_hook]}
        )

        get_driver().on_shutdown(client.aclose)
        return client
