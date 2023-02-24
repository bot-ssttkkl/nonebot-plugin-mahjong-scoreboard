from typing import Any, Callable, Optional

from pydantic.fields import Undefined


class DictField:
    def __init__(self, *, name: str = '',
                 default: Any = Undefined,
                 default_factory: Optional[Callable[[], Any]] = None):
        self.name = name
        self.default = default
        self.default_factory = default_factory

    def __set_name__(self, owner, name):
        if not self.name:
            self.name = name

    def __get__(self, instance, owner):
        x = instance.get(self.name, self.default)
        if x == Undefined and self.default_factory:
            return self.default_factory()
        return x

    def __set__(self, instance, value):
        instance[self.name] = value
