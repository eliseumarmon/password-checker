import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import path from 'node:path';
import { expect, test } from '@playwright/test';

// The API cannot reset to empty, so each welcome test owns a fresh backend.
// Forwarding its API keeps the browser on an origin accepted by the origin guard.
export const welcomeTest = test.extend<{ emptyWorkspace: void }>({
  emptyWorkspace: [async ({ page }, use) => {
    const root = path.resolve(import.meta.dirname, '../..');
    const python = process.env.E2E_PYTHON
      ?? path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    const server = spawn(python, ['-u', '-c', [
      'import socket, uvicorn',
      "sock = socket.socket(); sock.bind(('127.0.0.1', 0)); sock.listen(128)",
      'print(sock.getsockname()[1], flush=True)',
      "uvicorn.Server(uvicorn.Config('backend.password_checker.api:app', log_level='error')).run(sockets=[sock])",
    ].join('\n')], { cwd: root, stdio: ['ignore', 'pipe', 'inherit'] });
    const terminated = new Promise<string>(resolve => {
      server.once('error', error => resolve(error.message));
      server.once('exit', (code, signal) => resolve(`exit code ${code}, signal ${signal}`));
    });
    const lines = createInterface({ input: server.stdout });
    try {
      let startupTimer: ReturnType<typeof setTimeout> | undefined;
      let port: string;
      try {
        port = await Promise.race([
          once(lines, 'line').then(([line]) => line as string),
          terminated.then(reason => { throw new Error(`Isolated server failed to start: ${reason}`); }),
          new Promise<never>((_, reject) => {
            startupTimer = setTimeout(() => reject(new Error('Isolated server did not report its port')), 10000);
          }),
        ]);
      } finally {
        clearTimeout(startupTimer);
      }
      const url = `http://127.0.0.1:${port}`;
      await Promise.race([
        expect.poll(async () => {
          try { return (await page.request.get(`${url}/api/workspace`)).ok(); } catch { return false; }
        }).toBe(true),
        terminated.then(reason => { throw new Error(`Isolated server failed to start: ${reason}`); }),
      ]);
      // Only browser requests are forwarded; page.request still targets the shared server.
      // Do not use shared-server API helpers in welcomeTest.
      await page.route('**/api/**', async route => {
        const requestUrl = new URL(route.request().url());
        const response = await route.fetch({ url: `${url}${requestUrl.pathname}${requestUrl.search}` });
        await route.fulfill({ response });
      });
      await use();
    } finally {
      lines.close();
      if (server.exitCode === null && server.signalCode === null) server.kill();
      const force = setTimeout(() => server.kill('SIGKILL'), 2000);
      let deadline: ReturnType<typeof setTimeout> | undefined;
      try {
        await Promise.race([
          terminated,
          new Promise<never>((_, reject) => {
            deadline = setTimeout(() => reject(new Error('Isolated server did not exit')), 4000);
          }),
        ]);
      } finally {
        clearTimeout(force);
        clearTimeout(deadline);
      }
    }
  }, { auto: true }],
});
