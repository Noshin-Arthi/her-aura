import { defineConfig, devices } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const PORT = 8000;
const E2E_DB = path.resolve(__dirname, '..', 'e2e.db');

// Fresh database per run (main process only; workers also load this file).
if (!process.env.TEST_WORKER_INDEX) {
  try { fs.rmSync(E2E_DB, { force: true }); } catch { /* server from a previous run may still hold it */ }
}
const python = process.env.PYTHON ?? 'python';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Mobile viewport runs only the @mobile-tagged suites (booking shares slot data, so it runs once).
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] }, grep: /@mobile/ },
  ],
  // Starts the app with its own throwaway database before the tests run.
  webServer: {
    command: `"${python}" -m uvicorn app.main:app --port ${PORT}`,
    cwd: path.resolve(__dirname, '..'),
    url: `http://127.0.0.1:${PORT}/healthz`,
    reuseExistingServer: !process.env.CI,
    env: { DATABASE_URL: 'sqlite:///./e2e.db', SECRET_KEY: 'e2e-secret', AD_SECONDS: '2' },  // short ads keep tests fast
  },
});
