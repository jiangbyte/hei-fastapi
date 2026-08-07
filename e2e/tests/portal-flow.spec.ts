/** Author: Charlie */

import { expect, test } from "@playwright/test";

test("portal login page supports auth flow shell", async ({ page }) => {
  await page.route("**/api/v1/portal/captcha**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: { captcha_id: "c1", image: "data:image/svg+xml;base64,YQ==" },
      }),
    });
  });
  await page.route("**/api/v1/portal/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: {
          account_id: "p1",
          account: "user",
          account_type: "PORTAL",
          nickname: "User",
          role_ids: [],
          dept_ids: [],
          group_ids: [],
          profile: {},
        },
      }),
    });
  });

  await page.goto("/auth/login");
  await expect(page).toHaveURL(/\/auth\/login/);
  await expect(page.locator("input").first()).toBeVisible({ timeout: 15_000 });
  // Portal 首屏不得显示仅管理端可见的 MFA 开通文案。
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/开始开通 MFA|otpauth/i);
});
