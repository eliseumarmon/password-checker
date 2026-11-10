import { expect, test, type Page } from '@playwright/test';

// Fictional records only: a Netflix conflict group and two exact Amazon copies.
const csv = [
  'name,url,username,password,note',
  'Netflix,https://netflix.invalid/,ana,fictional-old-111,',
  'Netflix,https://netflix.invalid/,ana,fictional-new-222,',
  'Amazon,https://amazon.invalid/,ana,fictional-card-333,',
  'Amazon,https://amazon.invalid/,ana,fictional-card-333,',
].join('\n');

type Row = { id: string; name: string; included: boolean };

async function workspace(page: Page) {
  const response = await page.request.get('/api/workspace');
  expect(response.ok()).toBe(true);
  return response.json();
}

async function seed(page: Page) {
  const response = await page.request.post('/api/import', {
    multipart: { files: { name: 'chrome.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) } },
  });
  expect(response.ok()).toBe(true);
  await page.goto('/');
}

const notice = (page: Page) => page.getByRole('status', { name: 'Último cambio' });
const table = (page: Page) => page.locator('.desktop-table');
const headerUndo = (page: Page) => page.getByRole('button', { name: '↶ Deshacer' });

async function confirmWith(page: Page, label: string) {
  const dialog = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await dialog.getByRole('button', { name: label, exact: true }).click();
  await expect(dialog).toBeHidden();
}

async function openAll(page: Page, count: number) {
  await page.getByRole('tab', { name: `Todas (${count})` }).click();
}

async function trashAmazonFromItsRow(page: Page) {
  await openAll(page, 4);
  await table(page).getByRole('row', { name: /Amazon/ }).first().getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(notice(page)).toContainText('«Amazon» en la papelera.');
}

test('saving a record names the changed fields, never their values, and its Deshacer restores the record', async ({ page }) => {
  await seed(page);
  await openAll(page, 4);
  await table(page).getByRole('row', { name: /Netflix/ }).first().getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await editor.getByRole('textbox', { name: /^Contraseña/ }).fill('fictional-saved-999');
  await editor.getByLabel('Notas').fill('fictional-note-777');
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(editor).toBeHidden();

  const description = '«Netflix» guardada. Cambió: Contraseña y Notas.';
  await expect(notice(page)).toContainText(description);
  await expect(notice(page)).not.toContainText('fictional-saved-999');
  await expect(notice(page)).not.toContainText('fictional-note-777');
  await expect(headerUndo(page)).toHaveAttribute('title', `Deshacer: ${description}`);

  await notice(page).getByRole('button', { name: 'Deshacer', exact: true }).click();
  await expect(notice(page)).toContainText(`Se deshizo: ${description}`);
  await expect(notice(page).getByRole('button', { name: 'Deshacer', exact: true })).toHaveCount(0);
  const netflix = (await workspace(page)).records.filter((r: Row) => r.name === 'Netflix');
  for (const { id } of netflix) {
    const detail = await (await page.request.get(`/api/records/${id}`)).json();
    expect(['fictional-old-111', 'fictional-new-222']).toContain(detail.password);
    expect(detail.note).toBe('');
  }
  await expect(headerUndo(page)).toBeDisabled();
  await expect(headerUndo(page)).toHaveAttribute('title', 'Deshacer último cambio');
});

test('every operation shows its own notice, replacing the previous one', async ({ page }) => {
  await seed(page);
  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  await confirmWith(page, 'Fusionar');
  await expect(notice(page)).toContainText('Copias exactas fusionadas: 1 registro a la papelera.');
  await expect(notice(page)).toHaveCount(1);

  await table(page).getByRole('button', { name: 'Mover grupo a la papelera' }).click();
  await confirmWith(page, 'Mover a la papelera');
  await expect(notice(page)).toContainText('2 registros de «Netflix» en la papelera.');
  await expect(notice(page)).toHaveCount(1);

  await page.locator('.sidebar').getByRole('button', { name: /Papelera/ }).click();
  await table(page).getByRole('row', { name: /Netflix/ }).first().getByRole('button', { name: 'Restaurar' }).click();
  await expect(notice(page)).toContainText('«Netflix» restaurada.');
  await expect(notice(page)).toHaveCount(1);

  await page.locator('.sidebar').getByRole('button', { name: /Credenciales/ }).click();
  await openAll(page, 2);
  await table(page).getByRole('row', { name: /Amazon/ }).getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(notice(page)).toContainText('«Amazon» en la papelera.');
  await expect(notice(page)).toHaveCount(1);

  // The header button and the shortcut also leave their own notice.
  await page.getByRole('tab', { name: 'Todas (1)' }).focus();
  await page.keyboard.press('Control+z');
  await expect(notice(page)).toContainText('Se deshizo: «Amazon» en la papelera.');
  await headerUndo(page).click();
  await expect(notice(page)).toContainText('Se deshizo: «Netflix» restaurada.');
  await expect(notice(page)).toHaveCount(1);
});

test('saving without changes shows no new notice', async ({ page }) => {
  await seed(page);
  await trashAmazonFromItsRow(page);
  const step = (await workspace(page)).last_change.id;
  await table(page).getByRole('row', { name: /Netflix/ }).first().getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(editor).toBeHidden();
  await expect(notice(page)).toContainText('«Amazon» en la papelera.');
  await expect(notice(page).getByRole('button', { name: 'Deshacer', exact: true })).toBeEnabled();
  expect((await workspace(page)).last_change.id).toBe(step);
});

test('a notice whose step is no longer the last one turns its button off', async ({ page }) => {
  await seed(page);
  await trashAmazonFromItsRow(page);
  // Another tab saves a record: the page does not know yet.
  const netflix = (await workspace(page)).records.find((r: Row) => r.name === 'Netflix');
  expect((await page.request.patch(`/api/records/${netflix.id}`, { data: { review: 'reviewed' } })).ok()).toBe(true);
  const other = (await workspace(page)).last_change.id;

  await notice(page).getByRole('button', { name: 'Deshacer', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('El último cambio ya no es el que se muestra en pantalla');
  await expect(notice(page)).toContainText('«Amazon» en la papelera.');
  await expect(notice(page).getByRole('button', { name: 'Deshacer', exact: true })).toBeDisabled();
  await expect(headerUndo(page)).toHaveAttribute('title', 'Deshacer: «Netflix» guardada. Cambió: Estado de revisión.');
  const state = await workspace(page);
  expect(state.last_change.id).toBe(other);
  expect(state.records.filter((r: Row) => r.name === 'Amazon' && !r.included)).toHaveLength(1);
});

test('the notice shows inside the comparison while it is open', async ({ page }) => {
  await seed(page);
  await table(page).getByRole('button', { name: 'Comparar' }).first().click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  await compare.getByRole('button', { name: 'Descartar' }).first().click();
  const inside = compare.getByRole('status', { name: 'Último cambio' });
  await expect(inside).toContainText('en la papelera.');
  await expect(page.locator('.page-notices').getByRole('status', { name: 'Último cambio' })).toHaveCount(0);
  await compare.getByRole('button', { name: 'Restaurar' }).click();
  await expect(inside).toContainText('restaurada.');
  await compare.getByRole('button', { name: 'Cerrar panel' }).click();
  await expect(page.locator('.page-notices').getByRole('status', { name: 'Último cambio' })).toContainText('restaurada.');
});

test('closing it, importing or opening a session takes the notice away', async ({ page }) => {
  await seed(page);
  await trashAmazonFromItsRow(page);
  await notice(page).getByRole('button', { name: 'Cerrar aviso de cambio' }).click();
  await expect(notice(page)).toHaveCount(0);

  await table(page).getByRole('row', { name: /Netflix/ }).first().getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(notice(page)).toContainText('«Netflix» en la papelera.');
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Importar otros CSV' }).click();
  await (await chooser).setFiles({ name: 'chrome.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) });
  await confirmWith(page, 'Importar');
  await expect(page.getByRole('tab', { name: 'Duplicados (2)' })).toBeVisible();
  await expect(notice(page)).toHaveCount(0);

  await trashAmazonFromItsRow(page);
  const passphrase = 'fictional-session-passphrase-12345';
  const saved = await page.request.post('/api/session/save', { data: { passphrase } });
  expect(saved.ok()).toBe(true);
  await page.locator('.sidebar').getByRole('button', { name: 'Ajustes' }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await dialog.getByLabel('Archivo cifrado').setInputFiles({ name: 'fictional.pwc', mimeType: 'application/octet-stream', buffer: await saved.body() });
  await dialog.getByLabel(/Contraseña de sesión/).fill(passphrase);
  await dialog.getByRole('button', { name: 'Abrir sesión' }).click();
  await confirmWith(page, 'Abrir sesión');
  await expect(dialog).toBeHidden();
  await expect(notice(page)).toHaveCount(0);
});

test('the notice and its buttons fit a 320 px screen', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await seed(page);
  await page.getByRole('tab', { name: 'Todas (4)' }).click();
  await page.locator('.mobile-cards').getByRole('button', { name: 'Mover a la papelera' }).first().click();
  await expect(notice(page)).toContainText('en la papelera.');
  for (const name of ['Deshacer', 'Cerrar aviso de cambio']) {
    const box = await notice(page).getByRole('button', { name, exact: true }).boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(320);
  }
  await notice(page).getByRole('button', { name: 'Deshacer', exact: true }).click();
  await expect(notice(page)).toContainText('Se deshizo:');
});

for (const [width, height] of [[320, 640], [1280, 720]]) {
  test(`the last record can scroll clear of the notice at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    const rows = Array.from({ length: 14 }, (_, n) => `Sitio ${String(n + 1).padStart(2, '0')},https://site-${n + 1}.invalid/,ana,fictional-pass-${n + 1}00,`);
    const imported = await page.request.post('/api/import', {
      multipart: { files: { name: 'many.csv', mimeType: 'text/csv', buffer: Buffer.from(['name,url,username,password,note', ...rows].join('\n')) } },
    });
    expect(imported.ok()).toBe(true);
    await page.goto('/');
    await page.getByRole('tab', { name: 'Todas (14)' }).click();
    const list = width > 760 ? page.locator('.desktop-table tbody tr') : page.locator('.mobile-cards > article');
    await list.first().getByRole('button', { name: 'Mover a la papelera' }).click();
    await expect(notice(page)).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    const last = list.last().getByRole('button', { name: 'Mover a la papelera' });
    const box = (await last.boundingBox())!;
    const top = (await page.locator('.page-notices').boundingBox())!.y;
    expect(box.y + box.height).toBeLessThanOrEqual(top);
  });
}
