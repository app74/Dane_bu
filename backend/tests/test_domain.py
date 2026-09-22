import pytest

from app.domain.iban import slovak_iban, validate_iban
from app.domain.identifiers import normalize_ic_dph, normalize_ico, normalize_oud


def test_identifiers_are_normalized_without_claiming_existence() -> None:
    assert normalize_ico(" 12345678 ") == "12345678"
    assert normalize_ic_dph("sk1234567890") == "SK1234567890"
    assert normalize_oud(" 1234567890 ") == "1234567890"

@pytest.mark.parametrize("value", ["123", "123456789", "abc1234567"])
def test_oud_rejects_invalid_syntax(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_oud(value)

def test_iban_has_valid_mod97() -> None:
    iban = slovak_iban("500224", "1234567890")
    assert iban == "SK1881805002241234567890"
    assert validate_iban(iban)

def test_iban_rejects_tampering() -> None:
    assert not validate_iban("SK1881805002241234567891")
