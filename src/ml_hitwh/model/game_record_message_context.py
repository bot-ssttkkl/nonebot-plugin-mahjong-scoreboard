from beanie import Document


class GameRecordMessageContext(Document):
    game_id: int
    message_id: int
    extra: dict = {}
