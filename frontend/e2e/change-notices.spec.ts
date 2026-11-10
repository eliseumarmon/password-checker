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

for (const [width, height] of [[1280, 720], [390, 760]]) {
  test(`inside the comparison the notice floats at the bottom of the window, never past the last record, at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    const variants = Array.from({ length: 10 }, (_, n) => `Netflix,https://netflix.invalid/,ana,fictional-variant-${n}00,`);
    const imported = await page.request.post('/api/import', {
      multipart: { files: { name: 'variants.csv', mimeType: 'text/csv', buffer: Buffer.from(['name,url,username,password,note', ...variants].join('\n')) } },
    });
    expect(imported.ok()).toBe(true);
    await page.goto('/');
    await page.getByRole('button', { name: /^Comparar/ }).first().click();
    const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
    const content = compare.locator('.dialog-content');
    await compare.getByRole('button', { name: 'Descartar' }).first().click();
    const toast = compare.getByRole('status', { name: 'Último cambio' });
    await expect(toast).toContainText('«Netflix» en la papelera.');

    // At the top of the list, it floats at the bottom of the visible part of the window.
    await content.evaluate(element => element.scrollTo(0, 0));
    await expect.poll(() => content.evaluate(element => element.scrollTop)).toBe(0);
    const view = (await content.boundingBox())!;
    const floating = (await toast.boundingBox())!;
    expect(floating.y + floating.height).toBeLessThanOrEqual(view.y + view.height);
    expect(floating.y + floating.height).toBeGreaterThan(view.y + view.height - 40);
    // As wide as its text, against the right edge.
    if (width > 760) expect(floating.width).toBeLessThan(view.width / 2);
    expect(Math.abs(floating.x + floating.width - (view.x + view.width))).toBeLessThan(40);

    // At the end, the last record's buttons stay above it.
    await content.evaluate(element => element.scrollTo(0, element.scrollHeight));
    await expect.poll(() => content.evaluate(element => element.scrollTop + element.clientHeight >= element.scrollHeight - 1)).toBe(true);
    const last = (await compare.locator('.compare-card').last().getByRole('button', { name: 'Ver / editar' }).boundingBox())!;
    expect(last.y + last.height).toBeLessThanOrEqual((await toast.boundingBox())!.y);
    await toast.getByRole('button', { name: 'Deshacer', exact: true }).click();
    await expect(toast).toContainText('Se deshizo: «Netflix» en la papelera.');
  });
}

test('in the comparison, Tab reaches the toast without leaving the dialog, and an error shows above it', async ({ page }) => {
  await seed(page);
  await table(page).getByRole('button', { name: 'Comparar' }).first().click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  await compare.getByRole('button', { name: 'Descartar' }).first().click();
  const toast = compare.getByRole('status', { name: 'Último cambio' });
  await expect(toast).toContainText('en la papelera.');

  // The dialog keeps focus inside: Tab goes round its controls, the toast's among them.
  const reached = new Set<string>();
  for (let press = 0; press < 30; press += 1) {
    await page.keyboard.press('Tab');
    const focus = await page.evaluate(() => {
      const active = document.activeElement;
      return { inDialog: !!active?.closest('.compare-dialog'), inToast: active?.closest('.change') ? active.textContent?.trim() ?? '' : '' };
    });
    expect(focus.inDialog).toBe(true);
    if (focus.inToast) reached.add(focus.inToast);
  }
  expect([...reached]).toEqual(expect.arrayContaining(['Deshacer', '×']));

  // A failed operation shows its error at the top of the dialog, above the toast.
  await page.route('**/api/records/*', route => route.request().method() === 'PATCH'
    ? route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"Fallo ficticio"}' })
    : route.continue());
  await compare.getByRole('button', { name: 'Descartar' }).first().click();
  const error = compare.getByRole('alert');
  await expect(error).toContainText('Fallo ficticio');
  await expect(toast).toContainText('en la papelera.');
  expect((await error.boundingBox())!.y + (await error.boundingBox())!.height).toBeLessThanOrEqual((await toast.boundingBox())!.y);
});

test('on the page the notice is as wide as its text, and the space beside it lets clicks through', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await seed(page);
  await trashAmazonFromItsRow(page);
  const box = (await notice(page).boundingBox())!;
  expect(box.width).toBeLessThan(480);
  expect(box.x + box.width).toBeGreaterThan(1280 - 40);
  // Just left of the notice, where the stack used to reach, the page underneath gets the click.
  const point = { x: box.x - 40, y: box.y + box.height / 2 };
  const inStack = await page.evaluate(({ x, y }) => !!document.elementFromPoint(x, y)?.closest('.page-notices'), point);
  expect(inStack).toBe(false);
});

for (const [width, height] of [[1280, 720], [390, 760], [320, 640]]) {
  test(`in the comparison the toast never covers the focused control, at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    const variants = Array.from({ length: 10 }, (_, n) => `Netflix,https://netflix.invalid/,ana,fictional-variant-${n}00,`);
    const imported = await page.request.post('/api/import', {
      multipart: { files: { name: 'variants.csv', mimeType: 'text/csv', buffer: Buffer.from(['name,url,username,password,note', ...variants].join('\n')) } },
    });
    expect(imported.ok()).toBe(true);
    await page.goto('/');
    await page.getByRole('button', { name: /^Comparar/ }).first().click();
    const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
    await compare.getByRole('button', { name: 'Descartar' }).first().click();
    await expect(compare.getByRole('status', { name: 'Último cambio' })).toContainText('en la papelera.');
    for (let press = 0; press < 40; press += 1) {
      await page.keyboard.press('Tab');
      const overlap = await page.evaluate(() => {
        const active = document.activeElement as HTMLElement | null;
        const toast = document.querySelector('.compare-dialog .change');
        if (!active || !toast || toast.contains(active)) return 0;
        const a = active.getBoundingClientRect();
        const t = toast.getBoundingClientRect();
        return Math.max(0, Math.min(a.bottom, t.bottom) - Math.max(a.top, t.top));
      });
      expect(overlap).toBe(0);
    }
  });
}
