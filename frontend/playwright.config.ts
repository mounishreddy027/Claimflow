import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '../e2e',
  timeout: 30000,
  reporter: [
    ['html', { outputFolder: '../playwright-report', open: 'never' }],
    ['json', { outputFile: '../playwright-report/results.json' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.UI_BASE_URL || 'http://localhost:3000',
    trace: 'on',
    screenshot: 'on',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
