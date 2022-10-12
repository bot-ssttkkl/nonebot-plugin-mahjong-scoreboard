from datetime import date


def encode_date(dt: date) -> int:
    return dt.year % 100 * 10000 + dt.month * 100 + dt.day


def decode_date(code: int) -> date:
    year = code // 10000 + 2000
    month = code // 100 % 100
    day = code % 100
    return date(year, month, day)


def count_digit(x: int) -> int:
    if x == 0:
        return 1
    n = 0
    while x > 0:
        n += 1
        x //= 10
    return n
