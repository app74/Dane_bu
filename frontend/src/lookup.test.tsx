import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./main";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("vyberie subjekt a uloží názov, skutočné DIČ a OÚD", async () => {
  const fetchMock = vi.fn((url: string, options?: RequestInit) =>
    Promise.resolve({
      ok: true,
      json: async () =>
        url.includes("/subject-lookup")
          ? {
              results: [
                {
                  name: "Žltý test",
                  ico: "00123456",
                  dic: "2012345678",
                  oud: "8026569576",
                  ic_dph: null,
                  address: "Bratislava",
                },
              ],
              source_url: "https://www.financnasprava.sk",
              registry_date: "2026-09-22",
              accounts_date: "2026-09-22",
            }
          : options?.method === "POST"
            ? { id: 5, ...JSON.parse(String(options.body)) }
            : [],
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);
  fireEvent.change(screen.getByLabelText("Vyhľadať podľa názvu, IČO alebo DIČ"), {
    target: { value: "00123456" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Vyhľadať subjekt" }));
  fireEvent.click(await screen.findByRole("button", { name: "Vybrať Žltý test" }));
  expect(screen.getByLabelText("Názov subjektu")).toHaveValue("Žltý test");
  expect(screen.getByLabelText("OÚD")).toHaveValue("8026569576");
  fireEvent.click(screen.getByRole("button", { name: "Uložiť subjekt" }));
  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/subjects$/),
      expect.objectContaining({
        body: JSON.stringify({
          name: "Žltý test",
          oud: "8026569576",
          ico: "00123456",
          dic: "2012345678",
          ic_dph: null,
        }),
      }),
    ),
  );
});

it("pri nedostupnom zdroji zobrazí chybu a ponechá ručné zadanie", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: !url.includes("/subject-lookup"),
        json: async () =>
          url.includes("/subject-lookup") ? { detail: "Zdroj je nedostupný." } : [],
      }),
    ),
  );
  render(<App />);
  fireEvent.change(screen.getByLabelText("Vyhľadať podľa názvu, IČO alebo DIČ"), {
    target: { value: "00123456" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Vyhľadať subjekt" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Zdroj je nedostupný.");
  expect(screen.getByLabelText("OÚD")).toBeEnabled();
});
