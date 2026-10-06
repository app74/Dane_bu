import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./main";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function setup() {
  const fetchMock = vi.fn(() => Promise.resolve({ ok: true, json: async () => [] }));
  vi.stubGlobal("fetch", fetchMock);
  const writeText = vi.fn(() => Promise.resolve());
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
  const open = vi.spyOn(window, "open").mockImplementation(() => null);
  render(<App />);
  return { fetchMock, writeText, open };
}

it("skopíruje rodné číslo, otvorí formulár FS a rodné číslo neodošle na backend", async () => {
  const { fetchMock, writeText, open } = setup();
  fireEvent.change(screen.getByLabelText("Rodné číslo"), { target: { value: "850101/1234" } });
  fireEvent.click(
    screen.getByRole("button", { name: "Skopírovať rodné číslo a otvoriť overenie OÚD" }),
  );
  expect(await screen.findByText(/Rodné číslo je v schránke/)).toBeInTheDocument();
  expect(writeText).toHaveBeenCalledWith("850101/1234");
  expect(open).toHaveBeenCalledWith(
    "https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/overenie-prideleneho-oud",
    "_blank",
    "noopener,noreferrer",
  );
  expect(screen.getByLabelText("Rodné číslo")).toHaveValue("");
  expect(JSON.stringify(fetchMock.mock.calls)).not.toContain("1234");
});

it.each(["85010112", "85010/11234", "8501011234567", "abcdef/1234"])(
  "odmietne neplatný tvar rodného čísla %s",
  (value) => {
    setup();
    fireEvent.change(screen.getByLabelText("Rodné číslo"), { target: { value } });
    expect(screen.getByRole("alert")).toHaveTextContent("Rodné číslo má tvar");
    expect(
      screen.getByRole("button", { name: "Skopírovať rodné číslo a otvoriť overenie OÚD" }),
    ).toBeDisabled();
  },
);

it("prijme deväťmiestne rodné číslo bez lomky", () => {
  setup();
  fireEvent.change(screen.getByLabelText("Rodné číslo"), { target: { value: "450101123" } });
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Skopírovať rodné číslo a otvoriť overenie OÚD" }),
  ).toBeEnabled();
});
