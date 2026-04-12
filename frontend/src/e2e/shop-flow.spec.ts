import { test, expect } from "@playwright/test";

test.describe("Shop Flow E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/shop");
    await page.waitForLoadState("networkidle");
  });

  test("shop page loads with header", async ({ page }) => {
    await expect(page.locator(".shop-page")).toBeVisible();
    await expect(page.locator(".wallet-pill")).toBeVisible();
  });

  test("shop page displays item cards grid", async ({ page }) => {
    await expect(page.locator(".shop-grid")).toBeVisible();
    const cards = page.locator(".shop-grid article");
    await expect(cards.first()).toBeVisible();
  });

  test("bag button is visible", async ({ page }) => {
    await expect(page.locator(".bag-btn")).toBeVisible();
  });

  test("shop hero section is visible", async ({ page }) => {
    await expect(page.locator(".shop-hero")).toBeVisible();
    await expect(page.locator(".shop-hero h1")).toBeVisible();
  });

  test("shop header has wallet balance", async ({ page }) => {
    await expect(page.locator(".wallet-pill strong")).toBeVisible();
  });

  test("shop has footer", async ({ page }) => {
    await expect(page.locator(".shop-footer")).toBeVisible();
  });
});
