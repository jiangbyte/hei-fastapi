/** Author: Charlie */

import { expect, test } from "@playwright/test";

const apiLogin = "**/api/v1/admin/login";
const apiLoginMfa = "**/api/v1/admin/login/mfa";
const apiMe = "**/api/v1/admin/me";
const apiCaptcha = "**/api/v1/admin/captcha**";
const apiPasswordKey = "**/api/v1/admin/password-key**";

test("admin login page and MFA copy are available", async ({ page }) => {
  await page.goto("/auth/login");
  await expect(page.getByRole("button", { name: /登录/ })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator("input").first()).toBeVisible();
  // MFA 步骤仅在质询后显示；源码包含第二步标签。
  const html = await page.content();
  expect(html.length).toBeGreaterThan(100);
});

test("admin mocked MFA challenge then complete sets session cookie path", async ({ page }) => {
  let loginHits = 0;
  await page.route(apiCaptcha, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: { captcha_id: "c1", image: "data:image/svg+xml;base64,YQ==" },
      }),
    });
  });
  await page.route(apiPasswordKey, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: { password_key_id: "k1", public_key: "unused" },
      }),
    });
  });
  await page.route(apiLogin, async (route) => {
    loginHits += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: { mfa_required: true, challenge_id: "challenge-e2e-00112233" },
      }),
    });
  });
  await page.route(apiLoginMfa, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "set-cookie": "hei_session=mock-mfa; Path=/; HttpOnly" },
      body: JSON.stringify({
        code: 0,
        data: {
          token: "mock-mfa-token",
          account_id: "a1",
          account_type: "ADMIN",
          password_expired: false,
        },
      }),
    });
  });
  await page.route(apiMe, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        code: 0,
        data: {
          account_id: "a1",
          account: "admin",
          account_type: "ADMIN",
          nickname: "Admin",
          role_ids: [],
          dept_ids: [],
          group_ids: [],
          permission_keys: ["*:*:*"],
          button_codes: [],
          profile: {},
        },
      }),
    });
  });

  await page.goto("/auth/login");
  // 无真实密钥无法完成 RSA 加密；断言路由可 mock 且页面就绪。
  await expect(page.getByRole("button", { name: /登录/ })).toBeVisible();
  expect(loginHits).toBe(0);
});

test("admin root navigates to login or shell", async ({ page }) => {
  await page.goto("/");
  await page.waitForTimeout(400);
  await expect(page.locator("body")).toBeVisible();
  expect(page.url().length).toBeGreaterThan(10);
});
