import { expect, test, type Locator, type Page } from '@playwright/test';
import { CHROMIUM_HEADER, chromiumRow, desktopTable, seed, showAllRecords } from './tables';

// Keyboard behavior of the comparison, record and session dialogs (keyboard-accessibility S3).

const editor = (page: Page) => page.getByRole('dialog', { name: 'Editar credencial' });
const compare = (page: Page) => page.getByRole('dialog', { name: 'Comparar duplicados' });
const session = (page: Page) => page.getByRole('dialog', { name: 'Sesión cifrada' });
const confirmation = (page: Page) => page.getByRole('alertdialog', { name: 'Confirmar acción' });
const rowAction = (page: Page, row: string, action: string) =>
  desktopTable(page).getByRole('row', { name: new RegExp(row) }).getByRole('button', { name: action, exact: true });

async function seedRecords(page: Page, ...names: string[]): Promise<void> {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...names.map((name, index) => chromiumRow(name, `user-${index}`))] }]);
  await showAllRecords(page, names.length);
}

async function seedGroups(page: Page, ...names: string[]): Promise<void> {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...names.flatMap(name => [chromiumRow(name, 'alice'), chromiumRow(name, 'alice')])] }]);
}

async function openWithKeyboard(page: Page, control: Locator): Promise<void> {
  await control.focus();
  await page.keyboard.press('Enter');
}

/** Tab and Shift+Tab, far past the number of controls, never leave the dialog. */
async function expectTabStaysInside(page: Page, dialog: Locator, presses = 16): Promise<void> {
  for (const key of ['Tab', 'Shift+Tab']) {
    for (let press = 0; press < presses; press++) {
      await page.keyboard.press(key);
      expect(await dialog.evaluate(element => element.contains(document.activeElement))).toBe(true);
    }
  }
}

test.describe('record dialog', () => {
  test('starts on the name, keeps Tab inside, closes with Escape and returns focus', async ({ page }) => {
    await seedRecords(page, 'Alpha', 'Bravo');
    const opener = rowAction(page, 'Bravo', 'Editar');
    await openWithKeyboard(page, opener);
    await expect(editor(page).getByLabel('Nombre')).toBeFocused();
    await expectTabStaysInside(page, editor(page));
    await page.keyboard.press('Escape');
    await expect(editor(page)).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test('reaches its save button with Tab', async ({ page }) => {
    await seedRecords(page, 'Alpha');
    await openWithKeyboard(page, rowAction(page, 'Alpha', 'Editar'));
    const save = editor(page).getByRole('button', { name: 'Guardar cambios' });
    await editor(page).getByRole('button', { name: 'Cancelar' }).focus();
    await page.keyboard.press('Tab');
    await expect(save).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(editor(page).getByRole('button', { name: 'Cerrar', exact: true })).toBeFocused();
    await page.keyboard.press('Shift+Tab');
    await expect(save).toBeFocused();
  });

  test('asks before Escape discards unsaved changes, and Escape only closes the top dialog', async ({ page }) => {
    await seedRecords(page, 'Alpha');
    const opener = rowAction(page, 'Alpha', 'Editar');
    await openWithKeyboard(page, opener);
    await editor(page).getByLabel('Nombre').fill('Alpha edited');
    await page.keyboard.press('Escape');
    await expect(confirmation(page)).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(confirmation(page)).toBeHidden();
    await expect(editor(page)).toBeVisible();
    await expect(editor(page).getByLabel('Nombre')).toHaveValue('Alpha edited');

    await page.keyboard.press('Escape');
    await confirmation(page).getByRole('button', { name: 'Descartar cambios' }).click();
    await expect(editor(page)).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test('moves focus to the next row, the previous one or the title when its row leaves', async ({ page }) => {
    await seedRecords(page, 'Alpha', 'Bravo', 'Charlie');
    const discard = async (row: string, left: number) => {
      await openWithKeyboard(page, rowAction(page, row, 'Editar'));
      await editor(page).getByRole('button', { name: 'Descartar' }).click();
      await expect(page.getByRole('button', { name: `Todas (${left})` })).toBeVisible();
    };
    await discard('Bravo', 2);
    await expect(rowAction(page, 'Charlie', 'Editar')).toBeFocused();
    await discard('Charlie', 1);
    await expect(rowAction(page, 'Alpha', 'Editar')).toBeFocused();
    await discard('Alpha', 0);
    await expect(page.getByRole('heading', { name: 'Explorar y consolidar' })).toBeFocused();
  });

  test('moves focus to the next card when its row leaves on a small screen', async ({ page }) => {
    await seedRecords(page, 'Alpha', 'Bravo', 'Charlie');
    await page.setViewportSize({ width: 390, height: 844 });
    const edit = (name: string) => page.locator('.mobile-cards .record-card', { hasText: name }).getByRole('button', { name: 'Editar →' });
    await openWithKeyboard(page, edit('Bravo'));
    await editor(page).getByRole('button', { name: 'Descartar' }).click();
    await expect(page.locator('.mobile-cards .record-card')).toHaveCount(2);
    await expect(edit('Charlie')).toBeFocused();
  });
});

test.describe('comparison dialog', () => {
  test('starts on its title, keeps Tab inside, closes with Escape and returns focus', async ({ page }) => {
    await seedGroups(page, 'Alpha', 'Bravo');
    const opener = rowAction(page, 'Bravo', 'Comparar');
    await openWithKeyboard(page, opener);
    await expect(compare(page).getByRole('heading', { name: 'Comparar registros' })).toBeFocused();
    await expectTabStaysInside(page, compare(page));
    await page.keyboard.press('Escape');
    await expect(compare(page)).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test('moves focus to the next group when its group leaves', async ({ page }) => {
    await seedGroups(page, 'Alpha', 'Bravo', 'Charlie');
    await openWithKeyboard(page, rowAction(page, 'Bravo', 'Comparar'));
    await compare(page).getByRole('button', { name: 'Descartar' }).first().click();
    await expect(page.getByRole('button', { name: 'Duplicados (2)' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(compare(page)).toBeHidden();
    await expect(rowAction(page, 'Charlie', 'Comparar')).toBeFocused();
  });
});

test.describe('session dialog', () => {
  test('starts on the passphrase when saving, keeps Tab inside, closes with Escape and returns focus', async ({ page }) => {
    await seedRecords(page, 'Alpha');
    const opener = page.getByRole('button', { name: 'Guardar sesión cifrada' });
    await openWithKeyboard(page, opener);
    await expect(session(page).getByLabel(/Contraseña de sesión/)).toBeFocused();
    await expectTabStaysInside(page, session(page));
    await page.keyboard.press('Escape');
    await expect(session(page)).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test('starts on the file field when opening a session', async ({ page }) => {
    await seedRecords(page, 'Alpha');
    await page.getByRole('button', { name: 'Ajustes' }).first().click();
    await openWithKeyboard(page, page.getByRole('button', { name: 'Abrir', exact: true }));
    await expect(session(page).getByLabel('Archivo cifrado')).toBeFocused();
  });
});
