from dataclasses import dataclass
from typing import TypeVar, List, Generic

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    data: List[T]
    total: int
