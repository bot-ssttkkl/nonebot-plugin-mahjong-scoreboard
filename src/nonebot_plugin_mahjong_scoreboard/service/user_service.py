from .mapper import map_user
from ..model import User
from ..repository import data_source
from ..repository.user import UserRepository


async def get_user(platform_user_id: str) -> User:
    session = data_source.session()
    repo = UserRepository(session)
    user = await repo.get(platform_user_id)
    return await map_user(user, session)
