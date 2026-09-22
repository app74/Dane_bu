import { test, expect } from "@playwright/test";

test("vyhľadanie, výber a uloženie subjektu podľa DIČ", async ({ page }) => {
  let saved: Record<string, unknown> | undefined;
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/subject-lookup") {
      expect(route.request().postDataJSON()).toEqual({ identifier: "2012345678" });
      await route.fulfill({ json: {
        results: [{ name: "Test vyhľadávania", ico: "00123456", dic: "2012345678", oud: "8026569576", ic_dph: null, address: "Bratislava" }],
        source_url: "https://www.financnasprava.sk", registry_date: "2026-09-22", accounts_date: "2026-09-22",
      } });
    } else if (path === "/subjects" && route.request().method() === "POST") {
      saved = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: { id: 1, ...saved } });
    } else await route.fulfill({ json: [] });
  });
  await page.goto("/");
  await page.getByLabel("Vyhľadať podľa názvu, IČO alebo DIČ").fill("2012345678");
  await page.getByRole("button", { name: "Vyhľadať subjekt" }).click();
  await page.getByRole("button", { name: "Vybrať Test vyhľadávania" }).click();
  await expect(page.getByLabel("OÚD", { exact: true })).toHaveValue("8026569576");
  await expect(page.getByLabel("Názov subjektu")).toHaveValue("Test vyhľadávania");
  await page.getByRole("button", { name: "Uložiť subjekt" }).click();
  await expect(page.getByLabel("Vybraný subjekt")).toHaveValue("1");
  expect(saved).toMatchObject({ ico: "00123456", dic: "2012345678", oud: "8026569576" });
});
