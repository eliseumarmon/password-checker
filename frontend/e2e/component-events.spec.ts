import { mkdir, writeFile } from 'node:fs/promises';
import { expect, test, type Locator, type Page, type TestInfo } from '@playwright/test';
import { welcomeTest } from './isolated-welcome';

const originalCsv = 'name,url,username,password,note\nExample,https://example.invalid/,alice,fake-password-123456,';
const replacementCsv = [
  'name,url,username,password,note',
  'Replacement,https://replacement.invalid/,bob,fake-password-654321,',
  'Other,https://other.invalid/,carol,fake-password-789012,',
].join('\n');

async function seedWorkspace(page: Page, csv = originalCsv) {
  const response = await page.request.post('/api/import', {
    multipart: { files: { name: 'example.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) } },
  });
  expect(response.ok()).toBe(true);
}

async function csvFile(testInfo: TestInfo, csv: string) {
  await mkdir(testInfo.outputDir, { recursive: true });
  const filename = testInfo.outputPath('replacement.csv');
  await writeFile(filename, csv);
  return filename;
}

async function chooseCsv(page: Page, filename: string, accept: boolean) {
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Importar otros CSV' }).click();
  await (await chooser).setFiles(filename);
  const confirmation = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await expect(confirmation).toContainText('Importar reemplazará la sesión actual');
  await confirmation.getByRole('button', { name: accept ? 'Importar' : 'Cancelar', exact: true }).click();
  await expect(confirmation).toBeHidden();
}

async function workspace(page: Page) {
  const response = await page.request.get('/api/workspace');
  expect(response.ok()).toBe(true);
  return response.json();
}

async function editName(page: Page, row: Locator, name: string) {
  await row.getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await editor.getByLabel('Nombre').fill(name);
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(row).toContainText(name);
}

welcomeTest('opens the session dialog from the welcome screen', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir sesión cifrada anterior' }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await expect(dialog.getByRole('heading', { name: 'Abrir sesión anterior' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await expect(dialog).toBeHidden();
});

welcomeTest('imports a CSV dropped on the welcome screen', async ({ page }) => {
  await page.goto('/');
  const dataTransfer = await page.evaluateHandle(csv => {
    const transfer = new DataTransfer();
    transfer.items.add(new File([csv], 'example.csv', { type: 'text/csv' }));
    return transfer;
  }, originalCsv);
  const dropzone = page.locator('.dropzone');
  const dragoverPrevented = await dropzone.evaluate(element => {
    const event = new DragEvent('dragover', { bubbles: true, cancelable: true });
    element.dispatchEvent(event);
    return event.defaultPrevented;
  });
  expect(dragoverPrevented).toBe(true);
  await dropzone.dispatchEvent('drop', { dataTransfer });
  await expect(page.getByRole('tab', { name: 'Todas (1)' })).toBeVisible();
  await page.getByRole('tab', { name: 'Todas (1)' }).click();
  const table = page.locator('.desktop-table');
  const original = table.getByRole('row', { name: /alice/ });
  await expect(original).toContainText('Example');
  await page.reload();
  await page.getByRole('tab', { name: 'Todas (1)' }).click();
  await expect(original).toContainText('Example');
});

test('reselects the same CSV after cancelling and replaces the workspace', async ({ page }, testInfo) => {
  await seedWorkspace(page);
  await page.goto('/');
  await page.getByRole('tab', { name: 'Todas (1)' }).click();
  const table = page.locator('.desktop-table');
  const original = table.getByRole('row', { name: /alice/ });
  await editName(page, original, 'Example reviewed');

  const replacement = await csvFile(testInfo, replacementCsv);
  const beforeCancel = await workspace(page);
  expect(beforeCancel.can_undo).toBe(true);
  await chooseCsv(page, replacement, false);
  expect(await workspace(page)).toEqual(beforeCancel);
  await expect(original).toContainText('Example reviewed');
  await chooseCsv(page, replacement, true);
  await expect(page.getByRole('tab', { name: 'Todas (2)' })).toBeVisible();
  expect((await workspace(page)).can_undo).toBe(false);
  await page.getByRole('tab', { name: 'Todas (2)' }).click();
  await expect(table).toContainText('bob');
  await expect(table).toContainText('carol');
  await expect(table).not.toContainText('alice');
});

test('keeps the workspace and undo history after cancelling an import and reloading', async ({ page }, testInfo) => {
  await seedWorkspace(page, replacementCsv);
  await page.goto('/');
  await page.getByRole('tab', { name: 'Todas (2)' }).click();
  const table = page.locator('.desktop-table');
  const replacementRow = table.getByRole('row', { name: /bob/ });
  await editName(page, replacementRow, 'Replacement reviewed');
  const beforeCancel = await workspace(page);
  expect(beforeCancel.can_undo).toBe(true);
  const original = await csvFile(testInfo, originalCsv);
  await chooseCsv(page, original, false);
  await page.reload();
  expect(await workspace(page)).toEqual(beforeCancel);
  await page.getByRole('tab', { name: 'Todas (2)' }).click();
  await expect(replacementRow).toContainText('Replacement reviewed');
  await expect(table).toContainText('carol');
  await expect(table).not.toContainText('alice');
  await page.getByRole('button', { name: /Deshacer/ }).click();
  await expect(replacementRow).toContainText('Replacement');
  await expect(replacementRow).not.toContainText('Replacement reviewed');
  await expect(table).toContainText('carol');
  await expect(table).not.toContainText('alice');
});

test('opens save and load session dialogs from settings', async ({ page }) => {
  await seedWorkspace(page);
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: 'Ajustes' }).click();
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(dialog.getByRole('heading', { name: 'Guardar sesión cifrada' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await expect(dialog.getByRole('heading', { name: 'Abrir sesión anterior' })).toBeVisible();
});
