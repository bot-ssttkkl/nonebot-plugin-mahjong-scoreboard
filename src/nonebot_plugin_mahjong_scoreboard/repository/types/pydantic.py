from typing import Type

from pydantic import BaseModel
from sqlalchemy import TypeDecorator, JSON


class PydanticModel(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, t_model: Type[BaseModel], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t_model = t_model

    def process_bind_param(self, value, dialect):
        return value.dict()

    def process_result_value(self, value, dialect):
        return self.t_model.parse_obj(value)
