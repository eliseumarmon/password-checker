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
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    // Port 5173 is allowed by the origin guard and keeps the user's app on 8000 untouched.
    command: `npm --prefix frontend run build && "${python}" -m uvicorn backend.password_checker.api:app --host 127.0.0.1 --port 5173`,
    cwd: root,
    url: 'http://127.0.0.1:5173/api/workspace',
    // Always a fresh build and an empty workspace.
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
