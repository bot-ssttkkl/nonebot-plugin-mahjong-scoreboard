from inspect import isawaitable
from io import StringIO
from typing import List, TypeVar, Callable, Awaitable, Union

T = TypeVar("T")


async def map_pagination(data: List[T],
                         data_mapper: Union[Callable[[T], Awaitable[str]], Callable[[T], str]],
                         page_size: int = 10,
                         spliter: str = "\n") -> List[str]:
    msgs = []

    pending = 0
    pending_msg_io = StringIO()

    for x in data:
        line = data_mapper(x)
        if isawaitable(line):
            line = await line

        pending_msg_io.write(line)
        pending_msg_io.write(spliter)
        pending += 1

        if 0 < page_size <= pending:
            msgs.append(pending_msg_io.getvalue().strip())
            pending = 0
            pending_msg_io = StringIO()

    if pending > 0:
        msgs.append(pending_msg_io.getvalue().strip())

    return msgs
