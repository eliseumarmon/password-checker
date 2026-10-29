import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

// The backend keeps one in-memory workspace per process, so tests run serially.
const root = path.resolve(import.meta.dirname, '..');
const python = process.env.E2E_PYTHON
  ?? path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');

export default defineConfig({
  testDir: 'e2e',
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `npm --prefix frontend run build && "${python}" app.py`,
    cwd: root,
    url: 'http://127.0.0.1:8000/api/workspace',
    // Always a fresh build and an empty workspace.
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
