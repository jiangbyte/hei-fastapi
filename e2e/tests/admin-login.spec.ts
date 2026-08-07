/** Author: Charlie */

import { expect, test } from "@playwright/test";

test("admin login page renders", async ({ page }) => {
  await page.goto("/auth/login");
  await expect(page).toHaveURL(/\/auth\/login/);
  // 表单骨架：用户名 + 密码（captcha 随配置可能不同）。
  const inputs = page.locator("input");
  await expect(inputs.first()).toBeVisible({ timeout: 15_000 });
  expect(await inputs.count()).toBeGreaterThanOrEqual(2);
  const body = await page.locator("body").innerText();
  expect(body.length).toBeGreaterThan(0);
});
