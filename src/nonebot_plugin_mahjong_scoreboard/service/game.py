from httpx import AsyncClient
from injector import singleton, inject
from mahjong_scoreboard_model import PlayerAndWind, Game

from nonebot_plugin_mahjong_scoreboard.service.auth import AuthFactory


@singleton
class GameService:
    @inject
    def __init__(self, client: AsyncClient, auth_factory: AuthFactory):
        self.client = client
        self.auth_factory = auth_factory

    async def new_game(self, group_id: int, player_and_wind: PlayerAndWind, platform: str, platform_id: str) -> Game:
        resp = await self.client.post(
            "/games/",
            data=dict(group_id=group_id, player_and_wind=player_and_wind),
            auth=self.auth_factory.platform_auth(platform, platform_id)
        )
        return Game.parse_obj(resp.json())
