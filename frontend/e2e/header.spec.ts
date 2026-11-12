import { expect, test } from '@playwright/test';
import { CHROMIUM_HEADER, chromiumRow, seed } from './tables';

// Fictional records only.
test('shows the four figures as one surface of readings, in the measured face', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Example', 'alice'), chromiumRow('Example', 'alice')] }]);
  const figures = page.locator('.metrics .metric');
  await expect(figures).toHaveCount(4);
  const boxes = await figures.evaluateAll(cells => cells.map(cell => cell.getBoundingClientRect().toJSON()));
  // Neighbouring cells meet at a hairline seam, so the four read as one panel.
  for (let i = 1; i < boxes.length; i++) expect(boxes[i].left - boxes[i - 1].right).toBeLessThanOrEqual(1);
  const faces = await page.locator('.metrics .metric strong').evaluateAll(values => values.map(value => getComputedStyle(value).fontFamily));
  for (const face of faces) expect(face).toMatch(/^"?Atkinson Hyperlegible Mono"?,/);
  await expect(page.locator('.topbar p')).toHaveText('Los originales no se modifican. Las contraseñas permanecen ocultas.');
});
