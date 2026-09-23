import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const { encodePayMock } = vi.hoisted(() => ({
  encodePayMock: vi.fn(() => "pay-by-square-payload"),
}));

vi.mock("bysquare/pay", () => ({
  CurrencyCode: { EUR: "EUR" },
  PaymentOptions: { PaymentOrder: "PaymentOrder" },
  encode: encodePayMock,
}));

vi.mock("qrcode", () => ({
  default: { toDataURL: vi.fn(() => Promise.resolve("data:image/png;base64,test")) },
}));

import { App } from "./main";

describe("úvodná obrazovka", () => {
  it("zobrazuje bezpečnostné upozornenie", () => {
    render(<div role="alert">Pred úhradou porovnajte údaje s oficiálnymi pokynmi.</div>);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("sprievodca", () => {
  it("načíta podporované pravidlá a subjekty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve({
          ok: true,
          json: async () =>
            url.endsWith("/subjects")
              ? [{ id: 1, name: "Test", oud: "1234567890" }]
              : url.endsWith("/tax-rules")
                ? [{ id: "income-return-2025", name: "Daň z príjmov z priznania za rok 2025" }]
                : [],
        }),
      ),
    );
    render(<App />);
    await waitFor(() => expect(screen.getByText(/Daň z príjmov/)).toBeInTheDocument());
    expect(screen.getByText(/Test/)).toBeInTheDocument();
  });

  it("ponúkne export vytvoreného náhľadu", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, options?: RequestInit) => {
        if (options?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              subject_name: "Test",
              oud: "1234567890",
              domestic_account: "500224-1234567890/8180",
              iban: "SK0000000000000000000000",
              variable_symbol: "1700992025",
              amount: "10.00",
              currency: "EUR",
              due_date: "2026-03-31",
              rule_name: "Daň z príjmov z priznania za rok 2025",
              source_url: "https://www.financnasprava.sk/source",
              last_verified: "2026-09-22",
              warning: "Overte údaje.",
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () =>
            url.endsWith("/subjects")
              ? [{ id: 1, name: "Test", oud: "1234567890" }]
              : url.endsWith("/tax-rules")
                ? [{ id: "income-return-2025", name: "Daň z príjmov z priznania za rok 2025" }]
                : [],
        });
      }),
    );
    const createObjectURL = vi.fn(() => "blob:test");
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    render(<App />);
    await waitFor(() => expect(screen.getByText(/Daň z príjmov/)).toBeInTheDocument());
    const amountInputs = screen.getAllByLabelText("Suma v EUR");
    fireEvent.change(amountInputs[amountInputs.length - 1], { target: { value: "10,00" } });
    const previewButtons = screen.getAllByRole("button", { name: "Vytvoriť náhľad" });
    await previewButtons[previewButtons.length - 1].click();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Exportovať TXT" })).toBeInTheDocument(),
    );
    screen.getByRole("button", { name: "Exportovať TXT" }).click();
    expect(createObjectURL).toHaveBeenCalledOnce();
  });

  it("neposiela názov daňového subjektu do poľa príjemcu QR platby", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, options?: RequestInit) =>
        Promise.resolve({
          ok: true,
          json: async () =>
            options?.method === "POST"
              ? {
                  subject_name: "Daňový subjekt s.r.o.",
                  oud: "1234567890",
                  iban: "SK0000000000000000000000",
                  variable_symbol: "1700992025",
                  amount: "10.00",
                  rule_name: "Daň z príjmov",
                }
              : url.endsWith("/subjects")
                ? [{ id: 1, name: "Daňový subjekt s.r.o.", oud: "1234567890" }]
                : [{ id: "income-return-2025", name: "Daň z príjmov" }],
        }),
      ),
    );

    render(<App />);
    await waitFor(() => expect(screen.getAllByText(/Daň z príjmov/).length).toBeGreaterThan(0));
    const amountInputs = screen.getAllByLabelText("Suma v EUR");
    fireEvent.change(amountInputs[amountInputs.length - 1], { target: { value: "10,00" } });
    const previewButtons = screen.getAllByRole("button", { name: "Vytvoriť náhľad" });
    await previewButtons[previewButtons.length - 1].click();

    await waitFor(() => expect(encodePayMock).toHaveBeenCalled());
    const qrCalls = encodePayMock.mock.calls as unknown as Array<[
      { payments: Array<{ beneficiary: { name: string } }> },
    ]>;
    const qrPayload = qrCalls[qrCalls.length - 1]?.[0];
    expect(qrPayload).toBeDefined();
    const payment = qrPayload?.payments[0];
    expect(payment).toBeDefined();
    expect(payment?.beneficiary).toEqual({ name: "" });
  });
});
