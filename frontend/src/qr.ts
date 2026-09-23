import { Version } from "bysquare";
import { CurrencyCode, encode as encodePay, PaymentOptions } from "bysquare/pay";

export type QrPayment = {
  amount: string;
  variable_symbol: string;
  iban: string;
  rule_name: string;
};

export function payBySquarePayload(payment: QrPayment): string {
  return encodePay(
    {
      payments: [
        {
          type: PaymentOptions.PaymentOrder,
          amount: Number(payment.amount),
          variableSymbol: payment.variable_symbol,
          currencyCode: CurrencyCode.EUR,
          beneficiary: { name: "" },
          bankAccounts: [{ iban: payment.iban }],
          paymentNote: payment.rule_name,
        },
      ],
    },
    // PAY by square 1.2.0 requires a beneficiary name; the recipient is intentionally
    // left empty, which format 1.1.0 allows. IBAN is validated (MOD 97) by the backend.
    { version: Version["1.1.0"] },
  );
}
