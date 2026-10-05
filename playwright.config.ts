import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E and MCP Evaluation Configuration
 * Configured for ClaimFlow autonomous browser evaluation
 * Supports separate Web UI (port 3000) and Backend API (port 8000)
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.UI_BASE_URL || 'http://localhost:3000',
    trace: 'on',
    screenshot: 'on',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn claimflow.main:app --port 8000 --app-dir backend/src',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 15000,
    },
    {
      command: 'python -m http.server 3000 --directory frontend',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 15000,
    },
  ],
});
