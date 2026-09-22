import { test, expect } from "@playwright/test";

test("úvodná stránka", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Platobné údaje pre dane" }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("hlavný scenár vytvorí náhľad", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Názov subjektu").fill("E2E subjekt");
  await page.getByLabel("OÚD").fill("8888888888");
  await page.getByRole("button", { name: "Uložiť subjekt" }).click();
  await expect(page.getByLabel("Potvrdené pravidlo")).not.toHaveValue("");
  await page.getByLabel("Suma v EUR").fill("10,00");
  await page.getByRole("button", { name: "Vytvoriť náhľad" }).click();
  await expect(
    page.getByRole("heading", { name: "Kontrolný náhľad" }),
  ).toBeVisible();
  await expect(page.locator(".result dd").nth(2)).toHaveText(/^\d{10}/);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportovať TXT" }).click();
  const download = await downloadPromise;
  await expect(download.suggestedFilename()).toBe("platobne-udaje.txt");
});

test("zrážková daň z dividend má potvrdené údaje", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Názov subjektu").fill("Platiteľ dividend");
  await page.getByLabel("OÚD").fill("9999999999");
  await page.getByRole("button", { name: "Uložiť subjekt" }).click();
  await expect(page.getByLabel("Potvrdené pravidlo")).not.toHaveValue("");
  await page
    .getByLabel("Potvrdené pravidlo")
    .selectOption("withholding-dividend-2026-05");
  await page.getByLabel("Suma v EUR").fill("1700,00");
  await page.getByRole("button", { name: "Vytvoriť náhľad" }).click();
  await expect(
    page.getByRole("heading", { name: "Kontrolný náhľad" }),
  ).toBeVisible();
  await expect(page.locator(".result dd").nth(2)).toHaveText(/^1700052026/);
});
