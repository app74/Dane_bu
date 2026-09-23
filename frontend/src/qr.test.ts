import { decode } from "bysquare/pay";
import { describe, expect, it } from "vitest";
import { payBySquarePayload } from "./qr";

// Uses the real bysquare library (no mock): the mocked UI test did not catch that
// format 1.2.0 rejects the intentionally empty beneficiary name.
const payment = {
  amount: "1700.50",
  variable_symbol: "1700992025",
  // Test OÚD 1234567890 with prefix 500224 (see docs/rules-sources.md); MOD 97 valid.
  iban: "SK1881805002241234567890",
  rule_name: "Daň z príjmov z priznania za rok 2025",
};

describe("PAY by square QR", () => {
  it("vytvorí QR údaje bez mena príjemcu", () => {
    expect(() => payBySquarePayload(payment)).not.toThrow();
  });

  it("zakóduje IBAN, sumu, VS a poznámku bez straty", () => {
    const decoded = decode(payBySquarePayload(payment)).payments[0];
    expect(decoded.bankAccounts[0].iban).toBe(payment.iban);
    expect(decoded.amount).toBe(1700.5);
    expect(decoded.variableSymbol).toBe(payment.variable_symbol);
    expect(decoded.currencyCode).toBe("EUR");
    expect(decoded.beneficiary?.name ?? "").toBe("");
  });
});
