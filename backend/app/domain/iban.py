from .identifiers import normalize_digits


def domestic_account(account_prefix: str, oud: str, bank_code: str = "8180") -> str:
    prefix = normalize_digits(account_prefix, name="predčíslie")
    base = normalize_digits(oud, name="OÚD", length=10)
    bank = normalize_digits(bank_code, name="kód banky", length=4)
    if len(prefix) > 6:
        raise ValueError("predčíslie môže mať najviac 6 číslic")
    return f"{prefix.zfill(6)}-{base}/{bank}"

def slovak_iban(account_prefix: str, oud: str, bank_code: str = "8180") -> str:
    domestic = domestic_account(account_prefix, oud, bank_code)
    prefix, rest = domestic.split("-")
    base, bank = rest.split("/")
    bban = f"{bank}{prefix}{base}"
    check = 98 - ((int(bban + "282000") % 97))
    iban = f"SK{check:02d}{bban}"
    if not validate_iban(iban):
        raise ValueError("Nepodarilo sa vytvoriť platný IBAN")
    return iban

def validate_iban(iban: str) -> bool:
    normalized = iban.replace(" ", "").upper()
    if len(normalized) != 24 or not normalized.startswith("SK") or not normalized[2:].isdigit():
        return False
    rearranged = normalized[4:] + "2820" + normalized[2:4]
    return int(rearranged) % 97 == 1
