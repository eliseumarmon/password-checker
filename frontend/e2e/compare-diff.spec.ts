import { expect, test } from '@playwright/test';
import { CHROMIUM_HEADER, desktopTable, seed } from './tables';

// Fictional records only: one account in two versions, with different passwords.
const rows = [CHROMIUM_HEADER,
  'Example,https://example.invalid/,alice,fake-first-123456,',
  'Example,https://example.invalid/,alice,fake-second-123456,'];

test('compares the versions of a group as a diff, field by field', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: rows }]);
  await desktopTable(page).getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  const second = compare.locator('.compare-card').nth(1);
  const marks = second.locator('.compare-flags');
  await expect(marks).toContainText('URL igual');
  await expect(marks).toContainText('Usuario igual');
  await expect(marks).toContainText('Contraseña distinta');
  await expect(marks.locator('.differs')).toHaveText(/Contraseña distinta/);
  await expect(second.locator('.compare-origin')).toHaveText(/^chrome, línea \d+$/);
});

test('opens the site from the record with a drawn icon, not an arrow in the label', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: rows }]);
  await page.getByRole('tab', { name: /^Todas/ }).click();
  await desktopTable(page).getByRole('button', { name: 'Editar' }).first().click();
  const open = page.getByRole('dialog', { name: 'Editar credencial' }).getByRole('button', { name: /Abrir sitio/ });
  await expect(open).toHaveText('Abrir sitio en pestaña nueva');
  await expect(open.locator('svg')).toHaveCount(1);
});

test('names each field with its own gender in the diff', async ({ page }) => {
  // Same site and password, two users: only the user differs.
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER,
    'Example,https://example.invalid/,alice,fake-shared-123456,', 'Example,https://example.invalid/,bob,fake-shared-123456,'] }]);
  await desktopTable(page).getByRole('button', { name: 'Comparar' }).click();
  const marks = page.getByRole('dialog', { name: 'Comparar duplicados' }).locator('.compare-card').nth(1).locator('.compare-flags');
  await expect(marks).toContainText('Usuario distinto');
  await expect(marks).toContainText('URL igual');
});
