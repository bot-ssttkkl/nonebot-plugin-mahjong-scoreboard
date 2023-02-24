from collections import UserDict as UserDictType
from typing import Type

from sqlalchemy import TypeDecorator, JSON


class UserDict(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dict_type: Type[UserDictType], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dict_type = dict_type

    def process_bind_param(self, value, dialect):
        return value.data

    def process_result_value(self, value, dialect):
        return self.dict_type(value)
