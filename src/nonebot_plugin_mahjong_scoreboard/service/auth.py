import asyncio
from typing import Callable, Awaitable

from cachetools import TTLCache
from httpx import AsyncClient, Auth
from injector import inject, singleton
from mahjong_scoreboard_model import Token

from nonebot_plugin_mahjong_scoreboard.config import Config
from nonebot_plugin_mahjong_scoreboard.inj import inj


@singleton
class AuthService:
    @inject
    def __init__(self, client: AsyncClient, conf: Config):
        self.client = client
        self.conf = conf

    async def bot_auth(self) -> Token:
        resp = await self.client.post(
            "/auth/bot-auth",
            data=dict(
                secret=self.conf.mahjong_scoreboard_api_secret
            ))
        body = Token.parse_obj(resp.json())
        return body

    async def platform_login(self, platform: str, platform_id: str) -> Token:
        auth_factory = inj().get(AuthFactory)
        resp = await self.client.post(
            "/auth/platform_login",
            data=dict(
                platform=platform,
                platform_id=platform_id
            ),
            auth=auth_factory.bot_auth()
        )
        body = Token.parse_obj(resp.json())
        return body


class TokenStore:
    def __init__(self, sign: Callable[[], Awaitable[str]]):
        self._lock = asyncio.Lock()
        self._token = None
        self.sign = sign

    async def refresh(self):
        async with self._lock:
            self._token = await self.sign()
            return self._token

    async def get(self):
        if self._token is None:
            async with self._lock:
                if self._token is None:
                    self._token = await self.sign()

        return self._token


class TokenAuth(Auth):
    requires_request_body = True

    def __init__(self, sign: Callable[[], Awaitable[str]]):
        self.token_store = TokenStore(sign)

    def sync_auth_flow(self, request):
        raise NotImplementedError()

    async def async_auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {await self.token_store.get()}"
        response = yield request
        if response.status_code == 401:
            request.headers["Authorization"] = f"Bearer {await self.token_store.refresh()}"
            yield request


@singleton
class AuthFactory:
    def __init__(self):
        self._bot_auth = None
        self._platform_auth = TTLCache(maxsize=4096, ttl=7200)

    def bot_auth(self):
        if self._bot_auth is None:
            async def sign():
                auth_service = inj().get(AuthService)
                token = await auth_service.bot_auth()
                return token.access_token

            self._bot_auth = TokenAuth(sign)

        return self._bot_auth

    def platform_auth(self, platform: str, platform_id: str):
        if (platform, platform_id) not in self._platform_auth:
            async def sign():
                auth_service = inj().get(AuthService)
                token = await auth_service.platform_login(platform, platform_id)
                return token.access_token

            self._platform_auth[(platform, platform_id)] = TokenAuth(sign)

        return self._platform_auth[(platform, platform_id)]
