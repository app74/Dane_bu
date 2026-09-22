import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./main";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("blokuje dvojité odoslanie a nepridáva existujúci subjekt druhýkrát", async () => {
  const subject = { id: 1, name: "Test", oud: "8026760001" };
  let finish!: (value: unknown) => void;
  const post = vi.fn(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, options?: RequestInit) =>
      options?.method === "POST"
        ? post()
        : Promise.resolve({
            ok: true,
            json: async () => (url.endsWith("/subjects") ? [subject] : []),
          }),
    ),
  );
  render(<App />);
  await screen.findByRole("option", { name: "Test (8026760001)" });
  fireEvent.change(screen.getByLabelText("Názov subjektu"), { target: { value: "Test" } });
  fireEvent.change(screen.getByLabelText("OÚD"), { target: { value: "8026760001" } });
  const button = screen.getByRole("button", { name: "Uložiť subjekt" });
  fireEvent.click(button);
  fireEvent.click(button);
  expect(post).toHaveBeenCalledTimes(1);
  await waitFor(() => expect(button).toBeDisabled());
  finish({ ok: true, status: 200, json: async () => subject });
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Subjekt"));
  expect(screen.getAllByRole("option", { name: "Test (8026760001)" })).toHaveLength(1);
});
