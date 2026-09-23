import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api";
import { AuthGate } from "./auth";

function reply(status: number, body: unknown) {
  return Promise.resolve({ ok: status < 400, status, json: async () => body });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("prihlásenie", () => {
  it("bez zapnutej ochrany zobrazí aplikáciu", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => reply(200, { enabled: false, authenticated: true })),
    );
    render(<AuthGate>obsah aplikácie</AuthGate>);
    expect(await screen.findByText("obsah aplikácie")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Odhlásiť sa" })).toBeNull();
  });

  it("pri zapnutej ochrane vyžaduje heslo a po prihlásení zobrazí aplikáciu", async () => {
    const fetchMock = vi.fn((url: string) =>
      url.endsWith("/auth/login")
        ? reply(200, { authenticated: true })
        : reply(200, { enabled: true, authenticated: false }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate>obsah aplikácie</AuthGate>);
    fireEvent.change(await screen.findByLabelText("Heslo"), { target: { value: "tajne-heslo" } });
    fireEvent.click(screen.getByRole("button", { name: "Prihlásiť sa" }));
    expect(await screen.findByText("obsah aplikácie")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Odhlásiť sa" })).toBeInTheDocument();
    const login = fetchMock.mock.calls.find(([url]) => url.endsWith("/auth/login"));
    expect(login).toBeDefined();
  });

  it("zobrazí chybu pri nesprávnom hesle", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        url.endsWith("/auth/login")
          ? reply(401, { detail: "Nesprávne heslo." })
          : reply(200, { enabled: true, authenticated: false }),
      ),
    );
    render(<AuthGate>obsah aplikácie</AuthGate>);
    fireEvent.change(await screen.findByLabelText("Heslo"), { target: { value: "zle" } });
    fireEvent.click(screen.getByRole("button", { name: "Prihlásiť sa" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Nesprávne heslo.");
    expect(screen.queryByText("obsah aplikácie")).toBeNull();
  });

  it("po vypršaní relácie (401) sa vráti na prihlásenie", async () => {
    const fetchMock = vi.fn((url: string) =>
      url.endsWith("/auth/status")
        ? reply(200, { enabled: true, authenticated: true })
        : reply(401, { detail: "Prihláste sa." }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate>obsah aplikácie</AuthGate>);
    await screen.findByText("obsah aplikácie");
    await apiFetch("/subjects");
    await waitFor(() => expect(screen.getByLabelText("Heslo")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("Relácia vypršala");
  });

  it("nenakonfigurovaný server zobrazí dôvod", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => reply(503, { detail: "Nastavte APP_PASSWORD." })),
    );
    render(<AuthGate>obsah aplikácie</AuthGate>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Nastavte APP_PASSWORD.");
  });
});
