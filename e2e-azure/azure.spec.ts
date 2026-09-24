import { expect, test } from "@playwright/test";

const entraUser = {
  "X-MS-CLIENT-PRINCIPAL-ID": "00000000-0000-0000-0000-00000000e2e0",
  "X-MS-CLIENT-PRINCIPAL-NAME": "e2e.tester@example.com",
};

test.describe("bez prihlásenia Microsoft Entra ID", () => {
  test("stránka ponúkne prihlásenie a API nevydá dáta", async ({
    page,
    request,
  }) => {
    await page.goto("/");
    await expect(
      page.getByRole("link", { name: "Prihlásiť sa účtom Microsoft" }),
    ).toBeVisible();
    await expect(page.getByLabel("Suma v EUR")).toHaveCount(0);
    expect((await request.get("/api/health")).status()).toBe(200);
    expect((await request.get("/api/subjects")).status()).toBe(401);
    expect((await request.get("/api/tax-rules")).status()).toBe(401);
  });
});

test.describe("prihlásený používateľ", () => {
  test.use({ extraHTTPHeaders: entraUser });

  test("hlavný scenár: subjekt, náhľad, QR, história a trvalosť dát", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/");
    await expect(
      page.getByText("Prihlásený: e2e.tester@example.com"),
    ).toBeVisible();

    await page.getByLabel("Názov subjektu").fill("Azure E2E subjekt");
    await page.getByLabel("OÚD", { exact: true }).fill("1234567890");
    await page.getByRole("button", { name: "Uložiť subjekt" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Subjekt bol uložený." }),
    ).toBeVisible();

    await page
      .getByLabel("Potvrdené pravidlo")
      .selectOption("income-return-2025");
    await page.getByLabel("Suma v EUR").fill("100,00");
    await page.getByRole("button", { name: "Vytvoriť náhľad" }).click();
    await expect(
      page.getByRole("heading", { name: "Kontrolný náhľad" }),
    ).toBeVisible();
    await expect(page.locator(".result dd").nth(2)).toHaveText("1700992025");
    const qr = page.getByRole("img", { name: "PAY by square QR kód" });
    await expect(qr).toBeVisible();
    expect(await qr.getAttribute("src")).toMatch(/^data:image\/png;base64,/);

    await page.getByRole("button", { name: "Uložiť do histórie" }).click();
    await expect(
      page.getByRole("button", { name: "Uložené v histórii" }),
    ).toBeVisible();

    await page.reload();
    await expect(page.getByRole("heading", { name: "História" })).toBeVisible();
    await expect(page.getByText(/VS 1700992025/)).toBeVisible();
    await expect(page.getByLabel("Vybraný subjekt")).toContainText(
      "Azure E2E subjekt",
    );
    expect(errors).toEqual([]);
  });

  test("vyhľadanie FS vypnuté v teste vráti hlásenie o ručnom zadaní", async ({
    request,
  }) => {
    const response = await request.post("/api/subject-lookup", {
      data: { identifier: "12345678" },
    });
    expect(response.status()).toBe(503);
    expect((await response.json()).detail).toContain("ručne");
  });

  test("splatnosť DPH: 25. deň nasledujúceho mesiaca, posun cez víkend a sviatky", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByLabel("Názov subjektu").fill("DPH splatnosť");
    await page.getByLabel("OÚD", { exact: true }).fill("8133492105");
    await page.getByRole("button", { name: "Uložiť subjekt" }).click();
    await expect(page.getByLabel("Vybraný subjekt")).toContainText(
      "DPH splatnosť",
    );
    await page
      .getByLabel("Vybraný subjekt")
      .selectOption({ label: "DPH splatnosť (8133492105)" });

    const dueFor = async (ruleId: string) => {
      await page.getByLabel("Potvrdené pravidlo").selectOption(ruleId);
      await page.getByLabel("Suma v EUR").fill("500,00");
      await page.getByRole("button", { name: "Vytvoriť náhľad" }).click();
      return page.locator(".result dd").nth(4);
    };

    await expect(await dueFor("vat-2026-month-08")).toContainText("25.9.2026");
    await expect(page.locator(".result dd").nth(5)).toHaveText(
      "DPH – august 2026",
    );
    await page.getByRole("button", { name: "Vytvoriť text e-mailu" }).click();
    await expect(page.locator(".print-preview pre")).toContainText(
      "Splatnosť:  25.9.2026",
    );

    // 25.12.2026 Friday and 26.12. are days of rest (seeded), 27.12. Sunday -> Monday 28.12.
    await expect(await dueFor("vat-2026-month-11")).toContainText("28.12.2026");
    await expect(await dueFor("vat-2026-quarter-02")).toContainText(
      "27.7.2026",
    );

    await page.getByText("Nastavenia splatnosti").click();
    const day = page.getByLabel("Deň splatnosti – DPH – mesačný platiteľ");
    await day.fill("20");
    await page
      .getByLabel("Posun na pracovný deň – DPH – mesačný platiteľ")
      .uncheck();
    await page
      .getByRole("row", { name: /DPH – mesačný platiteľ/ })
      .getByRole("button", { name: "Uložiť" })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: "Uložené" }),
    ).toBeVisible();
    await expect(await dueFor("vat-2026-month-08")).toContainText("20.9.2026");
    await page
      .getByRole("row", { name: /DPH – mesačný platiteľ/ })
      .getByRole("button", { name: "Predvolené" })
      .click();
    await expect(await dueFor("vat-2026-month-08")).toContainText("25.9.2026");
  });
});
