import { expect, test } from '@playwright/test';
import { CHROMIUM_HEADER, numberedRows, seed, showAllRecords } from './tables';

// Icons are drawn, never characters that a font may turn into emoji; labels carry no arrows.
test('draws the navigation, sort and page icons and keeps arrows out of the labels', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Site', 31)] }]);
  await showAllRecords(page, 31);
  const textOf = (selector: string) => page.locator(selector).evaluateAll(nodes => nodes.map(node => node.textContent!.trim()));
  await expect(page.locator('.sidebar nav .nav-icon svg')).toHaveCount(4);
  expect(await textOf('.sidebar nav .nav-icon')).toEqual(['', '', '', '']);
  expect(await textOf('.desktop-table .sort-icon')).not.toContain('↕');
  await expect(page.locator('.desktop-table .sort-icon svg').first()).toBeAttached();
  for (const name of ['Primera página', 'Página anterior', 'Página siguiente', 'Última página']) {
    const control = page.getByRole('button', { name, exact: true });
    await expect(control.locator('svg')).toHaveCount(1);
    await expect(control).toHaveText('');
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.mobile-nav button svg')).toHaveCount(4);
  for (const label of await textOf('.mobile-cards button')) expect(label).not.toContain('→');
});
