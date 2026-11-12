import { expect, test } from '@playwright/test';
import { welcomeTest } from './isolated-welcome';
import { CHROMIUM_HEADER, chromiumRow, seed } from './tables';

// Fictional records only. The other screens in the Console material: drawn icons, readings, rows instead of nested boxes.
welcomeTest('draws the welcome icon instead of a character', async ({ page }) => {
  await page.goto('/');
  const icon = page.locator('.dropzone .big-icon');
  await expect(icon.locator('svg')).toHaveCount(1);
  await expect(icon).toHaveText('');
});

test('lists the audit without dashes and sets its counts as readings', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, 'Weak,https://weak.invalid/,carol,fake-1,'] }]);
  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: /Auditoría/ }).click();
  const item = page.locator('.audit-block', { hasText: 'Contraseñas poco seguras' }).locator('.audit-item').first();
  await expect(item).toContainText('Weak');
  await expect(item).toContainText('carol');
  await expect(item).not.toContainText('—');
  await expect(page.locator('.audit-block', { hasText: 'Contraseñas poco seguras' }).locator('.audit-count')).toHaveText('1 credencial');
  const face = await page.locator('.audit-count .audit-figure').first().evaluate(count => getComputedStyle(count).fontFamily);
  expect(face).toMatch(/^"?Atkinson Hyperlegible Mono"?,/);
});

test('shows the records on a phone as rows, not boxes inside the panel', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Example', 'alice'), chromiumRow('Other', 'bob')] }]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('tab', { name: /^Todas/ }).click();
  const card = page.locator('.mobile-cards .record-card').first();
  const edges = await card.evaluate(box => { const style = getComputedStyle(box); return [style.borderLeftWidth, style.borderRightWidth, style.borderRadius]; });
  expect(edges).toEqual(['0px', '0px', '0px']);
});
