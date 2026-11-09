import { expect, test, type Page } from '@playwright/test';
import { CHROMIUM_HEADER, chromiumRow, desktopTable, seed } from './tables';

// Semantics and keyboard of the credential tabs and of the screen navigation (keyboard-accessibility S4).

const tab = (page: Page, name: RegExp) => page.getByRole('tab', { name });
const duplicates = (page: Page) => tab(page, /^Duplicados/);
const all = (page: Page) => tab(page, /^Todas/);

test.beforeEach(async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [
    CHROMIUM_HEADER, chromiumRow('Alpha', 'alice'), chromiumRow('Alpha', 'alice'), chromiumRow('Bravo', 'bob'),
  ] }]);
});

test('exposes the views as tabs that control one panel', async ({ page }) => {
  await expect(page.getByRole('tablist')).toHaveCount(1);
  await expect(page.getByRole('tab')).toHaveCount(2);
  await expect(duplicates(page)).toHaveAttribute('aria-selected', 'true');
  await expect(all(page)).toHaveAttribute('aria-selected', 'false');
  const panelId = await duplicates(page).getAttribute('aria-controls');
  await expect(all(page)).toHaveAttribute('aria-controls', panelId!);
  await expect(page.getByRole('tabpanel', { name: /^Duplicados/ })).toHaveAttribute('id', panelId!);
  await all(page).click();
  await expect(page.getByRole('tabpanel', { name: /^Todas/ })).toHaveAttribute('id', panelId!);
});

test('changes tab at once with the arrow keys and wraps around', async ({ page }) => {
  await duplicates(page).focus();
  await page.keyboard.press('ArrowRight');
  await expect(all(page)).toBeFocused();
  await expect(all(page)).toHaveAttribute('aria-selected', 'true');
  await expect(desktopTable(page).getByRole('row', { name: /Bravo/ })).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(duplicates(page)).toBeFocused();
  await expect(duplicates(page)).toHaveAttribute('aria-selected', 'true');
  await page.keyboard.press('ArrowLeft');
  await expect(all(page)).toBeFocused();
  await expect(all(page)).toHaveAttribute('aria-selected', 'true');
});

test('is a single Tab stop, on the selected tab', async ({ page }) => {
  await expect(duplicates(page)).toHaveAttribute('tabindex', '0');
  await expect(all(page)).toHaveAttribute('tabindex', '-1');
  await duplicates(page).focus();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('textbox', { name: 'Buscar credenciales' })).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(duplicates(page)).toBeFocused();
});

test('marks the current screen in the side navigation', async ({ page }) => {
  const navigation = page.getByRole('complementary', { name: 'Navegación principal' });
  await expect(navigation.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(navigation.getByRole('button', { name: 'Credenciales' })).toHaveAttribute('aria-current', 'page');
  await navigation.getByRole('button', { name: 'Auditoría' }).click();
  await expect(navigation.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(navigation.getByRole('button', { name: 'Auditoría' })).toHaveAttribute('aria-current', 'page');
});

test('marks the current screen in the mobile navigation', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const navigation = page.getByRole('navigation', { name: 'Navegación móvil' });
  await expect(navigation.getByRole('button', { name: 'Credenciales' })).toHaveAttribute('aria-current', 'page');
  await navigation.getByRole('button', { name: 'Ajustes' }).click();
  await expect(navigation.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(navigation.getByRole('button', { name: 'Ajustes' })).toHaveAttribute('aria-current', 'page');
});
