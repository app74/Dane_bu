import re

_DIGITS = re.compile(r"^\d+$")

def normalize_digits(value: str, *, name: str, length: int | None = None) -> str:
    normalized = value.strip().replace(" ", "")
    if not _DIGITS.fullmatch(normalized):
        raise ValueError(f"{name} musí obsahovať iba číslice")
    if length is not None and len(normalized) != length:
        raise ValueError(f"{name} musí mať {length} číslic")
    return normalized

def normalize_ico(value: str) -> str:
    return normalize_digits(value, name="IČO", length=8)

def normalize_dic(value: str) -> str:
    return normalize_digits(value, name="DIČ", length=10)

def normalize_ic_dph(value: str) -> str:
    normalized = value.strip().upper().replace(" ", "")
    if not re.fullmatch(r"SK\d{10}", normalized):
        raise ValueError("IČ DPH musí mať tvar SK a 10 číslic")
    return normalized

def normalize_oud(value: str) -> str:
    return normalize_digits(value, name="OÚD", length=10)
