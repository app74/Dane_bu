import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Settings } from "./settings";

const vatRow = {
  key: "vat-month",
  label: "DPH – mesačný platiteľ",
  kind: "next_month_day",
  day: 25,
  shift_to_workday: true,
  description: "25. deň mesiaca nasledujúceho po skončení obdobia",
  basis: "§ 78 ods. 1 zákona č. 222/2004 Z.z.",
  is_default: true,
};

function mockApi() {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      calls.push({ url, init });
      const json = url.includes("/settings/due-dates/")
        ? { ...vatRow, ...JSON.parse(String(init?.body ?? "{}")), is_default: false }
        : url.endsWith("/settings/due-dates")
          ? [vatRow]
          : init?.method === "POST"
            ? JSON.parse(String(init.body))
            : { holidays: [{ day: "2026-12-25", name: "Prvý sviatok vianočný" }] };
      return Promise.resolve({ ok: true, status: 200, json: async () => json });
    }),
  );
  return calls;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("nastavenia splatnosti", () => {
  it("zobrazí pravidlo DPH a uloží zmenený deň", async () => {
    const calls = mockApi();
    render(<Settings />);
    const day = await screen.findByLabelText("Deň splatnosti – DPH – mesačný platiteľ");
    expect(day).toHaveValue(25);
    expect(screen.getByLabelText("Posun na pracovný deň – DPH – mesačný platiteľ")).toBeChecked();
    fireEvent.change(day, { target: { value: "20" } });
    fireEvent.click(screen.getByRole("button", { name: "Uložiť" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Uložené"));
    const put = calls.find((call) => call.init?.method === "PUT");
    expect(put?.url).toContain("/settings/due-dates/vat-month");
    expect(JSON.parse(String(put?.init?.body))).toEqual({
      kind: "next_month_day",
      day: 20,
      shift_to_workday: true,
    });
  });

  it("zobrazí sviatky a pridá nový deň", async () => {
    const calls = mockApi();
    render(<Settings />);
    expect(await screen.findByText(/25\.12\.2026 – Prvý sviatok vianočný/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Dátum sviatku"), { target: { value: "2026-12-26" } });
    fireEvent.change(screen.getByLabelText("Názov sviatku"), {
      target: { value: "Druhý sviatok vianočný" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Pridať sviatok" }));
    expect(await screen.findByText(/26\.12\.2026 – Druhý sviatok vianočný/)).toBeInTheDocument();
    expect(calls.some((call) => call.init?.method === "POST")).toBe(true);
  });
});
