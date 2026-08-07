/** Author: Charlie */

import { expect, test } from "@playwright/test";

test("portal login page renders", async ({ page }) => {
  await page.goto("/auth/login");
  await expect(page).toHaveURL(/\/auth\/login/);
  await expect(page.locator("input").first()).toBeVisible({ timeout: 15_000 });
  const body = await page.locator("body").innerText();
  expect(body.length).toBeGreaterThan(0);
});
