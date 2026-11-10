import { expect, test, type Page } from '@playwright/test';

// Fictional records only.
const csv = [
  'name,url,username,password,note',
  'Netflix,https://netflix.invalid/,ana,fictional-old-111,',
  'Amazon,https://amazon.invalid/,ana,fictional-card-222,',
].join('\n');

async function workspace(page: Page) {
  const response = await page.request.get('/api/workspace');
  expect(response.ok()).toBe(true);
  return response.json();
}

/** Imports the records and renames Netflix through the API, leaving one undo step; returns its id. */
async function seedWithOneStep(page: Page): Promise<string> {
  const imported = await page.request.post('/api/import', {
    multipart: { files: { name: 'chrome.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) } },
  });
  expect(imported.ok()).toBe(true);
  const netflix = (await imported.json()).records.find((r: { name: string }) => r.name === 'Netflix');
  const edited = await page.request.patch(`/api/records/${netflix.id}`, { data: { name: 'Netflix (renamed)' } });
  expect(edited.ok()).toBe(true);
  return (await edited.json()).last_change.id;
}

/** Every undo the page asks the server for. */
function countUndoCalls(page: Page): string[] {
  const calls: string[] = [];
  page.on('request', request => { if (new URL(request.url()).pathname === '/api/undo') calls.push(request.method()); });
  return calls;
}

async function openAll(page: Page) {
  await page.goto('/');
  const tab = page.getByRole('tab', { name: 'Todas (2)' });
  await tab.click();
  return tab;
}

const table = (page: Page) => page.locator('.desktop-table');

for (const shortcut of ['Control+z', 'Meta+z']) {
  test(`${shortcut} undoes the last change when focus is outside a text field`, async ({ page }) => {
    await seedWithOneStep(page);
    const tab = await openAll(page);
    await expect(table(page)).toContainText('Netflix (renamed)');
    await tab.focus();
    await page.keyboard.press(shortcut);
    await expect(table(page)).not.toContainText('Netflix (renamed)');
    await expect(table(page)).toContainText('Netflix');
    expect((await workspace(page)).can_undo).toBe(false);
  });
}

test('keeps the native undo inside a text field', async ({ page }) => {
  const step = await seedWithOneStep(page);
  const calls = countUndoCalls(page);
  await openAll(page);
  const search = page.getByRole('textbox', { name: 'Buscar credenciales' });
  await search.click();
  await page.keyboard.type('ama');
  await page.keyboard.press('Control+z');
  await expect(search).not.toHaveValue('ama');
  await expect(table(page)).toContainText('Netflix (renamed)');
  expect((await workspace(page)).last_change.id).toBe(step);
  expect(calls).toEqual([]);
});

test('does nothing while a dialog is open', async ({ page }) => {
  const step = await seedWithOneStep(page);
  const calls = countUndoCalls(page);
  await openAll(page);
  await table(page).getByRole('row', { name: /Amazon/ }).getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await editor.getByRole('button', { name: 'Cerrar' }).focus();
  await page.keyboard.press('Control+z');
  await expect(editor).toBeVisible();
  await editor.getByRole('button', { name: 'Cerrar' }).click();
  await expect(editor).toBeHidden();

  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  const confirmation = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await expect(confirmation).toBeVisible();
  await page.keyboard.press('Control+z');
  await expect(confirmation).toBeVisible();
  await confirmation.getByRole('button', { name: 'Cancelar' }).click();
  await expect(confirmation).toBeHidden();

  expect((await workspace(page)).last_change.id).toBe(step);
  expect(calls).toEqual([]);
});

test('ignores Shift, Alt and a held key: each press undoes one step', async ({ page }) => {
  const first = await seedWithOneStep(page);
  const amazon = (await workspace(page)).records.find((r: { name: string }) => r.name === 'Amazon');
  expect((await page.request.patch(`/api/records/${amazon.id}`, { data: { review: 'reviewed' } })).ok()).toBe(true);
  const calls = countUndoCalls(page);
  const tab = await openAll(page);
  await tab.focus();
  await page.keyboard.press('Control+Shift+z');
  await page.keyboard.press('Control+Alt+z');

  await page.keyboard.down('Control');
  await page.keyboard.down('z');
  await expect.poll(async () => (await workspace(page)).last_change?.id).toBe(first);
  await page.keyboard.down('z'); // the key repeats while held
  await page.keyboard.up('z');
  await page.keyboard.press('z'); // a new press undoes the next step
  await page.keyboard.up('Control');
  await expect.poll(async () => (await workspace(page)).can_undo).toBe(false);
  expect(calls).toHaveLength(2);
});

test('refuses to undo a step another tab already moved past, and shows the current state', async ({ page }) => {
  const shown = await seedWithOneStep(page);
  const tab = await openAll(page);
  await expect(table(page)).toContainText('Netflix (renamed)');
  // Another tab renames Amazon: this page still shows the rename of Netflix as the last change.
  const amazon = (await workspace(page)).records.find((r: { name: string }) => r.name === 'Amazon');
  expect((await page.request.patch(`/api/records/${amazon.id}`, { data: { name: 'Amazon (tarjeta)' } })).ok()).toBe(true);
  const other = (await workspace(page)).last_change.id;
  expect(other).not.toBe(shown);
  await tab.focus();
  await page.keyboard.press('Control+z');
  await expect(page.getByRole('alert')).toContainText('El último cambio ya no es el que se muestra en pantalla');
  await expect(table(page)).toContainText('Amazon (tarjeta)');
  await expect(table(page)).toContainText('Netflix (renamed)');
  expect((await workspace(page)).last_change.id).toBe(other);
  // Now the page is up to date, so the header button undoes the step it describes.
  await page.getByRole('button', { name: 'Cerrar mensaje de error' }).click();
  await page.getByRole('button', { name: '↶ Deshacer' }).click();
  await expect(table(page)).not.toContainText('Amazon (tarjeta)');
  expect((await workspace(page)).last_change.id).toBe(shown);
});

test('does nothing, and shows no error, when there is nothing to undo', async ({ page }) => {
  await seedWithOneStep(page);
  expect((await page.request.post('/api/undo')).ok()).toBe(true);
  const calls = countUndoCalls(page);
  const tab = await openAll(page);
  await tab.focus();
  await page.keyboard.press('Control+z');
  await expect(table(page)).toContainText('Netflix');
  await expect(page.getByRole('alert')).toHaveCount(0);
  expect(calls).toEqual([]);
});
