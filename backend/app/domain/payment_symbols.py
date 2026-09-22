import re


class InvalidPaymentSymbol(ValueError):
    pass


def validate_vs(value: str) -> str:
    if not re.fullmatch(r"\d{10}", value):
        raise InvalidPaymentSymbol("Variabilný symbol musí mať presne 10 číslic")
    return value


def monthly_vs(prefix: str, year: int, month: int) -> str:
    if prefix != "1100":
        raise InvalidPaymentSymbol("Nepotvrdené predčíslie VS pre mesačné obdobie")
    if not 1 <= month <= 12 or not 1000 <= year <= 9999:
        raise InvalidPaymentSymbol("Neplatné mesačné obdobie")
    return validate_vs(f"{prefix}{month:02d}{year:04d}")


def quarterly_vs(prefix: str, year: int, quarter: int) -> str:
    if prefix != "1100":
        raise InvalidPaymentSymbol("Nepotvrdené predčíslie VS pre štvrťročné obdobie")
    if not 1 <= quarter <= 4 or not 1000 <= year <= 9999:
        raise InvalidPaymentSymbol("Neplatné štvrťročné obdobie")
    return validate_vs(f"{prefix}{40 + quarter:02d}{year:04d}")
