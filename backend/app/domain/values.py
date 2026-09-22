from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class EuroAmount:
    value: Decimal

    @classmethod
    def parse(cls, raw: str) -> "EuroAmount":
        try:
            value = Decimal(raw.strip().replace(",", "."))
        except (InvalidOperation, AttributeError):
            raise ValueError("Suma musí byť platné číslo") from None
        if not value.is_finite() or value < 0 or value.as_tuple().exponent < -2:
            raise ValueError("Suma musí byť nezáporná a mať najviac 2 desatinné miesta")
        return cls(value.quantize(Decimal("0.01")))


@dataclass(frozen=True)
class TaxPeriod:
    year: int
    month: int | None = None
    quarter: int | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.year <= 9999:
            raise ValueError("Rok obdobia nie je platný")
        if (self.month is None) == (self.quarter is None):
            raise ValueError("Obdobie musí byť mesiac alebo štvrťrok")
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValueError("Mesiac obdobia nie je platný")
        if self.quarter is not None and not 1 <= self.quarter <= 4:
            raise ValueError("Štvrťrok obdobia nie je platný")
