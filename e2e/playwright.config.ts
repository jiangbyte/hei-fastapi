/** Author: Charlie */

import { defineConfig, devices } from "@playwright/test";

const adminPort = 4173;
const portalPort = 4174;
const adminBase = `http://127.0.0.1:${adminPort}`;
const portalBase = `http://127.0.0.1:${portalPort}`;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    ...devices["Desktop Chrome"],
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `pnpm --dir ../web/admin exec vite preview --host 127.0.0.1 --port ${adminPort}`,
      url: adminBase,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `pnpm --dir ../web/portal exec vite preview --host 127.0.0.1 --port ${portalPort}`,
      url: portalBase,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "admin-chromium",
      testMatch: /admin-.*\.spec\.ts/,
      use: { baseURL: adminBase },
    },
    {
      name: "portal-chromium",
      testMatch: /portal-.*\.spec\.ts/,
      use: { baseURL: portalBase },
    },
  ],
});
