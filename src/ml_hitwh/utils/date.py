from datetime import date


def encode_date(dt: date) -> int:
    return dt.year % 100 * 10000 + dt.month * 100 + dt.day


def decode_date(code: int) -> date:
    year = code // 10000 + 2000
    month = code // 100 % 100
    day = code % 100
    return date(year, month, day)
