import { expect, test } from '@playwright/test';

// The typefaces ship with the app: nothing is requested from another origin (docs/guia-visual.md §2.2).
test('loads its own typefaces from its own origin', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => requests.push(request.url()));
  await page.goto('/');
  const loaded = await page.evaluate(async () => {
    const families = ['Host Grotesk', 'Atkinson Hyperlegible Mono'];
    const faces = await Promise.all(families.map(family => document.fonts.load(`16px "${family}"`)));
    return faces.map(list => list.length);
  });
  expect(loaded).toEqual([1, 1]);
  const origin = new URL(page.url()).origin;
  expect(requests.filter(url => !url.startsWith(origin) && !url.startsWith('data:'))).toEqual([]);
  expect(requests.filter(url => url.endsWith('.ttf'))).toHaveLength(2);
});

test('sets its text and its secrets in those typefaces', async ({ page }) => {
  await page.goto('/');
  const families = await page.evaluate(() => {
    const probe = document.createElement('span');
    probe.className = 'secret-input';
    probe.innerHTML = '<input type="password">';
    document.body.append(probe);
    const result = [getComputedStyle(document.body).fontFamily, getComputedStyle(probe.querySelector('input')!).fontFamily];
    probe.remove();
    return result;
  });
  expect(families[0]).toMatch(/^"?Host Grotesk"?,/);
  expect(families[1]).toMatch(/^"?Atkinson Hyperlegible Mono"?,/);
});
