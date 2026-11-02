import { readFile } from 'node:fs/promises';
import { expect, test, type Locator, type Page } from '@playwright/test';

// Fictional credentials only, built in memory: real exports never touch the repo.
const CHROME_CSV = [
  'name,url,username,password,note',
  'Example,https://example.invalid/login,alice,fake-Shared-123456,first',
  'Example,https://example.invalid/login,alice,fake-Shared-123456,second',
  'Conflict,https://conflict.invalid/,bob,fake-One-1234567,',
  'Conflict,https://conflict.invalid/,bob,fake-Two-1234567,',
].join('\n');
const BRAVE_CSV = [
  'name,url,username,password,note',
  ',android://SIGN@com.example.app/,eve,fake-App-1234567,',
  'Weak,https://weak.invalid/,carol,fake-123,',
].join('\n');

async function importFixtures(page: Page) {
  page.on('dialog', dialog => dialog.accept());
  await page.goto('/');
  await page.locator('input[type=file][accept*=".csv"]').first().setInputFiles([
    { name: 'chrome.csv', mimeType: 'text/csv', buffer: Buffer.from(CHROME_CSV) },
    { name: 'brave.csv', mimeType: 'text/csv', buffer: Buffer.from(BRAVE_CSV) },
  ]);
  await expect(page.getByRole('button', { name: 'Todas (6)' })).toBeVisible();
}

function paginationCsv(count: number, duplicates = false): string {
  const rows = Array.from({ length: count }, (_, index) => {
    const number = String(index).padStart(2, '0');
    return `Site ${number},https://site-${number}.invalid/,user-${number},fake-password-123456,`;
  });
  return ['name,url,username,password,note', ...rows.flatMap(row => duplicates ? [row, row] : [row])].join('\n');
}

async function seedPaginationRows(page: Page, count: number, duplicates = false, trash = false): Promise<void> {
  const imported = await page.request.post('/api/import', {
    multipart: { files: { name: 'pagination.csv', mimeType: 'text/csv', buffer: Buffer.from(paginationCsv(count, duplicates)) } },
  });
  expect(imported.ok()).toBe(true);
  if (trash) {
    const ids = (await imported.json()).records.map((record: { id: string }) => record.id);
    const moved = await page.request.post('/api/records/trash', { data: { ids } });
    expect(moved.ok()).toBe(true);
  }
  await page.reload();
}

async function expectThirtyRowsPerPage(page: Page, count: number): Promise<void> {
  const table = page.locator('.desktop-table');
  await expect(table.locator('tbody tr')).toHaveCount(30);
  const paginator = table.locator('.p-paginator');
  await expect(paginator).toHaveCount(count === 31 ? 1 : 0);
  if (count === 31) {
    await paginator.locator('.p-paginator-next').click();
    await expect(table.locator('tbody tr')).toHaveCount(1);
  }
}

function metric(page: Page, label: string): Locator {
  return page.locator('.metric', { hasText: label }).locator('strong');
}

// WCAG 2.x contrast ratio between the text and its first opaque ancestor background.
function contrastOf(cell: Locator): Promise<number> {
  return cell.evaluate(element => {
    const rgb = (value: string) => (value.match(/[\d.]+/g) ?? []).map(Number);
    const luminance = ([r, g, b]: number[]) => {
      const channel = (c: number) => {
        const s = c / 255;
        return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
    };
    let node: Element | null = element;
    let background = 'rgb(255, 255, 255)';
    while (node) {
      const color = getComputedStyle(node).backgroundColor;
      const alpha = rgb(color)[3];
      if (color !== 'transparent' && (alpha === undefined || alpha > 0)) {
        background = color;
        break;
      }
      node = node.parentElement;
    }
    const [light, dark] = [luminance(rgb(getComputedStyle(element).color)), luminance(rgb(background))]
      .sort((a, b) => b - a);
    return (light + 0.05) / (dark + 0.05);
  });
}

test.beforeEach(async ({ page }) => importFixtures(page));

test('imports several CSV files and groups duplicates and conflicts', async ({ page }) => {
  await expect(metric(page, 'Credenciales')).toHaveText('6');
  await expect(page.getByRole('button', { name: 'Duplicados (2)' })).toBeVisible();
  const table = page.locator('.desktop-table');
  await expect(table.getByRole('row', { name: /Conflict/ })).toBeVisible();
  await expect(table.getByRole('row', { name: /Example/ })).toBeVisible();
});

test('paginates duplicate groups after 30', async ({ page }) => {
  for (const count of [30, 31]) {
    await seedPaginationRows(page, count, true);
    await expect(page.getByRole('button', { name: `Duplicados (${count})` })).toBeVisible();
    await expectThirtyRowsPerPage(page, count);
  }
});

test('paginates records after 30', async ({ page }) => {
  for (const count of [30, 31]) {
    await seedPaginationRows(page, count);
    await page.getByRole('button', { name: `Todas (${count})` }).click();
    await expectThirtyRowsPerPage(page, count);
  }
});

test('paginates trashed records after 30', async ({ page }) => {
  for (const count of [30, 31]) {
    await seedPaginationRows(page, count, false, true);
    await sidebar(page).getByRole('button', { name: /Papelera/ }).click();
    await expectThirtyRowsPerPage(page, count);
  }
});

test('shows Android apps in Bitwarden format', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const row = page.locator('.desktop-table').getByRole('row', { name: /com\.example\.app/ });
  await expect(row).toContainText('androidapp://com.example.app');
  await expect(row).toContainText('Android');
});

test('shows each credential type on mobile cards', async ({ page }) => {
  await page.setViewportSize({ width: 600, height: 800 });
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const cards = page.locator('.mobile-cards .record-card');
  const web = cards.filter({ has: page.getByText('carol', { exact: true }) });
  const android = cards.filter({ has: page.getByText('eve', { exact: true }) });

  await expect(page.locator('.desktop-table')).toBeHidden();
  await expect(web.locator('p.muted')).toBeVisible();
  await expect(web.locator('p.muted')).toHaveText(/^Web · /);
  await expect(android.locator('p.muted')).toBeVisible();
  await expect(android.locator('p.muted')).toHaveText(/^Android · /);

  const typeFilter = page.getByLabel('Filtrar tipo');
  await typeFilter.selectOption({ label: 'Solo Android' });
  await expect(android).toBeVisible();
  await expect(web).toHaveCount(0);
  await typeFilter.selectOption({ label: 'Solo web' });
  await expect(web).toBeVisible();
  await expect(android).toHaveCount(0);
});

test('keeps table cells readable on the dark theme', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const row = page.locator('.desktop-table tbody tr').first();
  for (const index of [1, 2, 3, 5]) {
    expect(await contrastOf(row.locator('td').nth(index))).toBeGreaterThanOrEqual(4.5);
  }
});

test('keeps drawer actions visible and saves edits', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 600 });
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /bob/ }).first()
    .getByRole('button', { name: 'Editar' }).click();
  const drawer = page.getByRole('dialog', { name: 'Editar credencial' });
  const save = drawer.getByRole('button', { name: 'Guardar cambios' });
  await expect(save).toBeInViewport();
  await expect(drawer.getByRole('button', { name: 'Cancelar' })).toBeInViewport();

  await drawer.getByLabel('Nombre').fill('Conflict renamed');
  await save.click();
  await expect(drawer).toBeHidden();
  await expect(page.locator('.desktop-table')).toContainText('Conflict renamed');
});

test('preserves review options and saves the selected state', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const row = page.locator('.desktop-table').getByRole('row', { name: /carol/ });
  await row.getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  const select = editor.getByLabel('Estado de revisión');
  await expect(select.locator('option')).toHaveText([
    'Pendiente', 'Revisada (sin verificar acceso)', 'Verificada manualmente', 'No funciona',
  ]);
  await expect(select).toHaveValue('pending');
  await select.selectOption('verified');
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(editor).toBeHidden();
  await expect(row).toContainText('Verificada');
  await row.getByRole('button', { name: 'Editar' }).click();
  await expect(select).toHaveValue('verified');
});

test('merges exact copies into the trash and can undo it', async ({ page }) => {
  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
  await expect(page.getByRole('button', { name: 'Todas (5)' })).toBeVisible();
  await page.getByRole('button', { name: /Deshacer/ }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
});

function sidebar(page: Page): Locator {
  return page.getByRole('complementary', { name: 'Navegación principal' });
}

test('trashes a row from its quick action and restores it from the trash', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(page.getByRole('button', { name: 'Todas (5)' })).toBeVisible();
  await expect(page.locator('.desktop-table')).not.toContainText('carol');

  const trashButton = sidebar(page).getByRole('button', { name: 'Papelera (1)' });
  await expect(trashButton).toHaveAttribute('title', 'Papelera (1)');
  await expect(trashButton.locator('svg')).toBeVisible();
  await trashButton.click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Papelera');
  const row = page.locator('.desktop-table').getByRole('row', { name: /carol/ });
  await row.getByRole('button', { name: 'Restaurar' }).click();
  await expect(page.getByText('La papelera está vacía.')).toBeVisible();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
  await expect(sidebar(page).getByRole('button', { name: 'Papelera (0)' })).toHaveAttribute('title', 'Papelera (0)');
});

test('discards a record from the editor into the trash', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor.getByRole('checkbox')).toHaveCount(0);
  await editor.getByRole('button', { name: 'Descartar' }).click();
  await expect(editor).toBeHidden();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
});

test('reviews a record from the audit without leaving the audit', async ({ page }) => {
  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: /Auditoría/ }).click();
  await page.locator('.audit-block', { hasText: 'Contraseñas poco seguras' }).getByRole('button', { name: 'Revisar' }).first().click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor).toBeVisible();
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Auditoría local');
});

test('opens the editor centred on the screen', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Editar' }).click();
  const box = await page.getByRole('dialog', { name: 'Editar credencial' }).boundingBox();
  const viewport = page.viewportSize()!;
  expect(Math.abs(box!.x + box!.width / 2 - viewport.width / 2)).toBeLessThan(10);
});

test('uses compact cards and rows and normal-sized checkboxes', async ({ page }) => {
  for (const card of await page.locator('.metric').all()) {
    expect((await card.boundingBox())!.height).toBeLessThanOrEqual(76);
  }
  const row = (await page.locator('.desktop-table tbody tr').first().boundingBox())!;
  expect(row.height).toBeLessThanOrEqual(56);
  const checkbox = (await page.getByRole('checkbox', { name: 'Solo pendientes' }).boundingBox())!;
  expect(Math.max(checkbox.width, checkbox.height)).toBeLessThanOrEqual(20);
});

test('collapses the sidebar to icons and remembers it', async ({ page }) => {
  const aside = sidebar(page);
  const width = async () => (await aside.boundingBox())!.width;
  await aside.getByRole('button', { name: 'Contraer menú' }).click();
  await expect.poll(width).toBeLessThanOrEqual(72);
  await aside.getByRole('button', { name: /Auditoría/ }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Auditoría local');

  await page.reload();
  await expect.poll(width).toBeLessThanOrEqual(72);
  await aside.getByRole('button', { name: 'Expandir menú' }).click();
  await expect.poll(width).toBeGreaterThan(200);
});

test('shows only cards, not the table, on narrow screens', async ({ page }) => {
  await page.setViewportSize({ width: 600, height: 800 });
  await expect(page.locator('.desktop-table')).toBeHidden();
  await expect(page.locator('.mobile-cards .record-card').first()).toBeVisible();
  const mobileNav = page.getByRole('navigation', { name: 'Navegación móvil' });
  await expect(mobileNav).toBeVisible();
  const trashButton = mobileNav.getByRole('button', { name: 'Papelera' });
  await expect(trashButton.locator('svg')).toBeVisible();
  await trashButton.click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Papelera');
});

test('trashes a whole duplicate group in one undoable step', async ({ page }) => {
  const table = page.locator('.desktop-table');
  await expect(table.getByRole('columnheader', { name: 'Acciones' })).toBeVisible();
  await table.getByRole('row', { name: /Conflict/ }).getByRole('button', { name: 'Mover grupo a la papelera' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('2');
  await expect(page.getByRole('button', { name: 'Duplicados (1)' })).toBeVisible();
  await page.getByRole('button', { name: /Deshacer/ }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
});

test('keeps the header, stats and sidebar visible while scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 420 });
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.mouse.wheel(0, 2000);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(100);
  await expect(page.getByRole('heading', { level: 1 })).toBeInViewport();
  await expect(page.getByRole('button', { name: 'Exportar Bitwarden' })).toBeInViewport();
  await expect(page.locator('.metric', { hasText: 'En la papelera' })).toBeInViewport();
  await expect(sidebar(page).getByRole('button', { name: /Ajustes/ })).toBeInViewport();
});

test('opens the comparison centred and the editor above it', async ({ page }) => {
  await page.locator('.desktop-table').getByRole('row', { name: /Conflict/ }).getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  const box = (await compare.boundingBox())!;
  expect(Math.abs(box.x + box.width / 2 - page.viewportSize()!.width / 2)).toBeLessThan(10);

  await compare.getByRole('button', { name: 'Ver / editar' }).first().click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  await expect(compare).toBeVisible();
});

test('keeps the comparison open after discarding one record', async ({ page }) => {
  await page.locator('.desktop-table').getByRole('row', { name: /Conflict/ }).getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  const cards = compare.locator('.compare-card');
  await cards.first().getByRole('button', { name: 'Descartar' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
  await expect(compare).toBeVisible();
  await expect(cards).toHaveCount(2);
  await expect(cards.first()).toContainText('En la papelera');
  await expect(cards.first().getByRole('button', { name: 'Descartar' })).toHaveCount(0);
  await expect(compare.locator('.compare-flags')).toHaveCount(0);
  await expect(compare).toContainText('Ya no quedan duplicados activos en este grupo.');

  await cards.nth(1).getByRole('button', { name: 'Ver / editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor.getByRole('button', { name: 'Descartar' })).toBeVisible();
  await editor.getByRole('button', { name: 'Cancelar' }).click();

  await cards.first().getByRole('button', { name: 'Restaurar' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
  await expect(cards.first().getByRole('button', { name: 'Descartar' })).toBeVisible();
  await expect(compare.locator('.compare-flags')).toHaveCount(2);
});

test('saves an encrypted session and opens it again', async ({ page }) => {
  const passphrase = 'fictional-session-passphrase';
  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('1');

  await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
  const saveDialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await saveDialog.getByLabel(/Contraseña de sesión/).fill(passphrase);
  await saveDialog.getByLabel('Confirmar contraseña').fill(passphrase + '-typo');
  await saveDialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  await expect(page.getByRole('alert')).toContainText('no coinciden');
  await saveDialog.getByLabel('Confirmar contraseña').fill(passphrase);
  const download = page.waitForEvent('download');
  await saveDialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  const saved = await download;
  const file = { name: saved.suggestedFilename(), mimeType: 'application/octet-stream', buffer: await readFile(await saved.path()) };
  await expect(saveDialog).toBeHidden();

  await page.getByRole('button', { name: /Deshacer/ }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
  await sidebar(page).getByRole('button', { name: 'Ajustes' }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  const loadDialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await loadDialog.getByLabel('Archivo cifrado').setInputFiles(file);
  await loadDialog.getByLabel(/Contraseña de sesión/).fill(passphrase);
  await loadDialog.getByRole('button', { name: 'Abrir sesión' }).click();
  await expect(loadDialog).toBeHidden();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Credenciales');
});

test('clears save session passwords after cancelling and reopening', async ({ page }) => {
  const open = page.getByRole('button', { name: 'Guardar sesión cifrada' });
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await open.click();
  await dialog.getByLabel(/Contraseña de sesión/).fill('fictional-session-passphrase');
  await dialog.getByLabel('Confirmar contraseña').fill('fictional-session-confirmation');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await expect(dialog).toHaveCount(0);

  await open.click();
  await expect(dialog.getByLabel(/Contraseña de sesión/)).toHaveValue('');
  await expect(dialog.getByLabel('Confirmar contraseña')).toHaveValue('');
});

test('clears load session password and file after closing and reopening', async ({ page }) => {
  const loadRequests: string[] = [];
  page.on('request', request => {
    if (request.url().endsWith('/api/session/load')) loadRequests.push(request.url());
  });
  await sidebar(page).getByRole('button', { name: 'Ajustes' }).click();
  const open = page.getByRole('button', { name: 'Abrir', exact: true });
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await open.click();
  const file = dialog.getByLabel('Archivo cifrado');
  await file.setInputFiles({ name: 'fictional-session.pwc', mimeType: 'application/octet-stream', buffer: Buffer.from('fictional encrypted session') });
  await dialog.getByLabel(/Contraseña de sesión/).fill('fictional-session-passphrase');
  await expect(file).toHaveValue(/fictional-session\.pwc$/);
  await dialog.getByRole('button', { name: 'Cerrar' }).click();
  await expect(dialog).toHaveCount(0);

  await open.click();
  await expect(dialog.getByLabel(/Contraseña de sesión/)).toHaveValue('');
  await expect(file).toHaveValue('');
  expect(await file.evaluate((input: HTMLInputElement) => input.files?.length)).toBe(0);
  await dialog.getByLabel(/Contraseña de sesión/).fill('fictional-session-passphrase');
  await dialog.getByRole('button', { name: 'Abrir sesión' }).click();
  await expect(page.getByRole('alert')).toContainText('Selecciona el archivo cifrado');
  expect(loadRequests).toEqual([]);
});

test('clears session fields after closing with the backdrop', async ({ page }) => {
  await sidebar(page).getByRole('button', { name: 'Ajustes' }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  const password = dialog.getByLabel(/Contraseña de sesión/);
  const confirmation = dialog.getByLabel('Confirmar contraseña');
  const file = dialog.getByLabel('Archivo cifrado');
  const backdrop = page.locator('.modal-overlay');

  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await password.fill('fictional-save-passphrase');
  await confirmation.fill('fictional-save-confirmation');
  await backdrop.click({ position: { x: 5, y: 5 } });
  await expect(dialog).toHaveCount(0);
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(password).toHaveValue('');
  await expect(confirmation).toHaveValue('');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();

  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await password.fill('fictional-load-passphrase');
  await file.setInputFiles({ name: 'fictional-session.pwc', mimeType: 'application/octet-stream', buffer: Buffer.from('fictional encrypted session') });
  await backdrop.click({ position: { x: 5, y: 5 } });
  await expect(dialog).toHaveCount(0);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await expect(password).toHaveValue('');
  await expect(file).toHaveValue('');
  expect(await file.evaluate((input: HTMLInputElement) => input.files?.length)).toBe(0);
});

test('keeps session fields empty when switching between save and load', async ({ page }) => {
  await page.route('**/api/session/save', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Fallo ficticio' }),
  }), { times: 1 });
  await sidebar(page).getByRole('button', { name: 'Ajustes' }).click();
  const save = page.getByRole('button', { name: 'Guardar', exact: true });
  const load = page.getByRole('button', { name: 'Abrir', exact: true });
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  const password = dialog.getByLabel(/Contraseña de sesión/);
  const confirmation = dialog.getByLabel('Confirmar contraseña');
  const file = dialog.getByLabel('Archivo cifrado');

  await save.click();
  await password.fill('fictional-save-passphrase');
  await confirmation.fill('fictional-save-passphrase');
  await dialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  await expect(page.getByRole('alert')).toContainText('Fallo ficticio');
  await expect(password).toHaveValue('fictional-save-passphrase');
  await expect(confirmation).toHaveValue('fictional-save-passphrase');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await load.click();
  await expect(password).toHaveValue('');
  await expect(file).toHaveValue('');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await save.click();
  await expect(password).toHaveValue('');
  await expect(confirmation).toHaveValue('');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();

  await load.click();
  await password.fill('fictional-load-passphrase');
  await file.setInputFiles({ name: 'fictional-session.pwc', mimeType: 'application/octet-stream', buffer: Buffer.from('fictional encrypted session') });
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await save.click();
  await expect(password).toHaveValue('');
  await expect(confirmation).toHaveValue('');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await load.click();
  await expect(password).toHaveValue('');
  await expect(file).toHaveValue('');
  expect(await file.evaluate((input: HTMLInputElement) => input.files?.length)).toBe(0);
});

test('shows and enforces the session password minimum', async ({ page }) => {
  await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  const passphrase = dialog.getByLabel(/Contraseña de sesión/);
  await expect(passphrase).toHaveAttribute('type', 'password');
  await expect(dialog.getByText('Contraseña de sesión (mínimo 12 caracteres)')).toBeVisible();
  await passphrase.fill('x'.repeat(11));
  await dialog.getByLabel('Confirmar contraseña').fill('x'.repeat(11));
  await dialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  await expect(page.getByRole('alert')).toContainText('al menos 12 caracteres');
  await passphrase.fill('x'.repeat(12));
  await dialog.getByLabel('Confirmar contraseña').fill('x'.repeat(12));
  const download = page.waitForEvent('download');
  await dialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  await download;
  await expect(dialog).toBeHidden();
});

test('shows the server reason when a download fails', async ({ page }) => {
  await page.route('**/api/export', route => route.fulfill({
    status: 409, contentType: 'application/json', body: JSON.stringify({ detail: 'No hay credenciales para exportar' }),
  }));
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  await expect(page.getByRole('alert')).toContainText('No hay credenciales para exportar');
});

for (const { name, body, contentType, secret } of [
  { name: 'object detail', body: JSON.stringify({ detail: { password: 'fictional-secret-object' } }), contentType: 'application/json', secret: 'fictional-secret-object' },
  { name: 'list detail', body: JSON.stringify({ detail: ['fictional-secret-list'] }), contentType: 'application/json', secret: 'fictional-secret-list' },
  { name: 'non-JSON response', body: 'fictional-secret-plain-text', contentType: 'text/plain', secret: 'fictional-secret-plain-text' },
]) {
  test(`shows a generic export error for ${name}`, async ({ page }) => {
    const downloads: string[] = [];
    page.on('download', download => downloads.push(download.suggestedFilename()));
    await page.route('**/api/export', route => route.fulfill({ status: 503, contentType, body }));

    await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
    const alert = page.getByRole('alert');
    await expect(alert).toContainText('No se pudo exportar (503)');
    await expect(alert).not.toContainText(secret);
    // Observe late download events for a bounded period after the error appears.
    await page.waitForTimeout(500);
    expect(downloads).toEqual([]);
  });
}

test('keeps session details for retry when saving fails', async ({ page }) => {
  const passphrase = 'fictional-session-passphrase';
  const downloads: string[] = [];
  page.on('download', download => downloads.push(download.suggestedFilename()));
  await page.route('**/api/session/save', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: { passphrase } }),
  }), { times: 1 });

  await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  const password = dialog.getByLabel(/Contraseña de sesión/);
  const confirmation = dialog.getByLabel('Confirmar contraseña');
  await password.fill(passphrase);
  await confirmation.fill(passphrase);
  await dialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();

  // The notice belongs inside the open session dialog, not floating behind it.
  const alert = dialog.getByRole('alert');
  await expect(alert).toContainText('No se pudo guardar la sesión (503)');
  await expect(alert).not.toContainText(passphrase);
  await expect(page.getByRole('alert')).toHaveCount(1);
  // Keep observing until after the error, before starting the successful retry.
  await page.waitForTimeout(500);
  expect(downloads).toEqual([]);
  await expect(dialog).toBeVisible();
  await expect(password).toHaveValue(passphrase);
  await expect(confirmation).toHaveValue(passphrase);

  const download = page.waitForEvent('download');
  await dialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  expect((await download).suggestedFilename()).toBe('password-checker-session.pwc');
  await expect(dialog).toBeHidden();
  expect(downloads).toEqual(['password-checker-session.pwc']);
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('shows errors above an open dialog', async ({ page }) => {
  await sidebar(page).getByRole('button', { name: 'Ajustes' }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await dialog.getByLabel(/Contraseña de sesión/).fill('fictional-session-passphrase');
  await dialog.getByRole('button', { name: 'Abrir sesión' }).click();
  const alert = page.getByRole('alert');
  await expect(alert).toContainText('Selecciona el archivo cifrado');
  // Visible is not enough: nothing (such as the dialog backdrop) may cover the message.
  const onTop = await alert.evaluate(element => {
    const box = element.getBoundingClientRect();
    return element.contains(document.elementFromPoint(box.left + 8, box.top + box.height / 2));
  });
  expect(onTop).toBe(true);
});

for (const { name, viewport } of [
  { name: 'desktop', viewport: { width: 1280, height: 800 } },
  { name: 'mobile', viewport: { width: 390, height: 844 } },
]) {
  test(`keeps the error notice clear of navigation and header on ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.route('**/api/export', route => route.fulfill({ status: 503, body: '' }));
    const exportButton = page.getByRole('button', { name: 'Exportar Bitwarden' });
    await exportButton.click();
    const alert = page.getByRole('alert');
    await expect(alert).toContainText('No se pudo exportar');
    const notice = (await alert.boundingBox())!;
    const header = (await page.locator('.sticky-head').boundingBox())!;
    expect(notice.y).toBeGreaterThanOrEqual(header.y + header.height);
    if (name === 'mobile') {
      const nav = page.getByRole('navigation', { name: 'Navegación móvil' });
      const navBox = (await nav.boundingBox())!;
      expect(notice.y + notice.height).toBeLessThanOrEqual(navBox.y);
      await nav.getByRole('button', { name: 'Ajustes' }).click();
      await expect(page.getByRole('heading', { name: 'Ajustes', exact: true }).first()).toBeVisible();
    } else {
      await exportButton.click();
    }
    await expect(alert).toBeVisible();
    await alert.getByRole('button', { name: 'Cerrar aviso' }).click();
    await expect(alert).toHaveCount(0);
  });

  test(`keeps a failed save accessible and retryable on ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.route('**/api/session/save', route => route.fulfill({ status: 503, body: '' }), { times: 1 });
    await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
    const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
    const password = dialog.getByLabel(/Contraseña de sesión/);
    const confirmation = dialog.getByLabel('Confirmar contraseña');
    const save = dialog.getByRole('button', { name: 'Descargar archivo cifrado' });
    await password.fill('fictional-session-passphrase');
    await confirmation.fill('fictional-session-passphrase');
    await save.click();
    const alert = dialog.getByRole('alert');
    await expect(alert).toContainText('No se pudo guardar la sesión');
    await expect(password).toHaveValue('fictional-session-passphrase');
    await expect(confirmation).toHaveValue('fictional-session-passphrase');
    for (const control of [password, confirmation, save]) {
      await control.scrollIntoViewIfNeeded();
      const unobstructed = await control.evaluate(element => {
        const box = element.getBoundingClientRect();
        const target = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
        return element === target || element.contains(target);
      });
      expect(unobstructed).toBe(true);
      const controlBox = (await control.boundingBox())!;
      const alertBox = (await alert.boundingBox())!;
      expect(controlBox.y).toBeGreaterThanOrEqual(alertBox.y + alertBox.height);
    }
    const download = page.waitForEvent('download');
    await save.click();
    expect((await download).suggestedFilename()).toBe('password-checker-session.pwc');
    await expect(dialog).toHaveCount(0);
  });
}

test('keeps a long notice between the header and navigation in a short viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 320 });
  const message = 'Error largo de prueba. '.repeat(100);
  await page.route('**/api/export', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: message }),
  }));
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  const alert = page.getByRole('alert');
  await expect(alert).toContainText(message);
  const box = (await alert.boundingBox())!;
  const header = (await page.locator('.sticky-head').boundingBox())!;
  const nav = (await page.getByRole('navigation', { name: 'Navegación móvil' }).boundingBox())!;
  expect(box.y).toBeGreaterThanOrEqual(header.y + header.height);
  expect(box.y + box.height).toBeLessThanOrEqual(nav.y);
  const close = alert.getByRole('button', { name: 'Cerrar aviso' });
  expect(await close.evaluate(element => {
    const box = element.getBoundingClientRect();
    return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
  })).toBe(true);
  const scrollable = await alert.locator('span').evaluate(element => element.scrollHeight > element.clientHeight);
  expect(scrollable).toBe(true);
  await close.focus();
  await page.keyboard.press('Enter');
  await expect(alert).toHaveCount(0);
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  await expect(alert).toBeVisible();
  await page.getByRole('navigation', { name: 'Navegación móvil' }).getByRole('button', { name: 'Ajustes' }).click();
  await page.waitForTimeout(6000);
  await expect(alert).toBeVisible();
});

test('moves the persistent notice into the active dialog', async ({ page }) => {
  await page.route('**/api/export', route => route.fulfill({ status: 503, body: '' }));
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  const alert = page.getByRole('alert');
  await expect(alert).toHaveCount(1);
  await page.locator('.desktop-table').getByRole('row', { name: /Conflict/ }).getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  await expect(compare.getByRole('alert')).toBeVisible();
  await expect(alert).toHaveCount(1);
  await compare.getByRole('button', { name: 'Ver / editar' }).first().click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor.getByRole('alert')).toBeVisible();
  await expect(alert).toHaveCount(1);
  await editor.getByLabel('Notas').fill('Edit remains usable');
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  await expect(compare.getByRole('alert')).toBeVisible();
  await compare.getByRole('button', { name: 'Cerrar panel' }).click();
  await expect(alert).toBeVisible();
  await alert.getByRole('button', { name: 'Cerrar aviso' }).click();
  await expect(alert).toHaveCount(0);
});

for (const viewport of [{ width: 320, height: 320 }, { width: 390, height: 250 }]) {
  test(`keeps the notice close control usable at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.route('**/api/export', route => route.fulfill({
      status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Error largo. '.repeat(100) }),
    }));
    await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
    const alert = page.getByRole('alert');
    await expect(alert).toBeVisible();
    const noticeBox = (await alert.boundingBox())!;
    const headerBox = (await page.locator('.sticky-head').boundingBox())!;
    const navBox = (await page.getByRole('navigation', { name: 'Navegación móvil' }).boundingBox())!;
    expect(noticeBox.y).toBeGreaterThanOrEqual(headerBox.y + headerBox.height);
    expect(noticeBox.y + noticeBox.height).toBeLessThanOrEqual(navBox.y);
    const close = alert.getByRole('button', { name: 'Cerrar aviso' });
    const closeBox = (await close.boundingBox())!;
    expect(closeBox.y).toBeGreaterThanOrEqual(noticeBox.y);
    expect(closeBox.y + closeBox.height).toBeLessThanOrEqual(noticeBox.y + noticeBox.height);
    expect(await close.evaluate(element => {
      const box = element.getBoundingClientRect();
      return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
    })).toBe(true);
    await close.click();
    await expect(alert).toHaveCount(0);
  });
}

for (const viewport of [{ width: 320, height: 320 }, { width: 390, height: 250 }, { width: 844, height: 250 }]) {
  test(`keeps failed save fields and retry usable at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.route('**/api/session/save', route => route.fulfill({
      status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Error largo. '.repeat(100) }),
    }), { times: 1 });
    await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
    const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
    const password = dialog.getByLabel(/Contraseña de sesión/);
    const confirmation = dialog.getByLabel('Confirmar contraseña');
    const save = dialog.getByRole('button', { name: 'Descargar archivo cifrado' });
    const value = 'fictional-session-passphrase';
    await password.fill(value);
    await confirmation.fill(value);
    await save.click();
    await expect(dialog.getByRole('alert')).toBeVisible();
    await expect(password).toHaveValue(value);
    await expect(confirmation).toHaveValue(value);
    for (const field of [password, confirmation]) {
      await field.scrollIntoViewIfNeeded();
      expect(await field.evaluate(element => {
        const box = element.getBoundingClientRect();
        return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
      })).toBe(true);
      await field.click();
      await field.fill(value);
    }
    await save.scrollIntoViewIfNeeded();
    expect(await save.evaluate(element => {
      const box = element.getBoundingClientRect();
      return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
    })).toBe(true);
    const download = page.waitForEvent('download');
    await save.click();
    expect((await download).suggestedFilename()).toBe('password-checker-session.pwc');
    await expect(dialog).toHaveCount(0);
  });
}

for (const viewport of [{ width: 320, height: 401 }, { width: 844, height: 401 }]) {
  test(`keeps editor fields clear of actions with a notice at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.getByRole('button', { name: 'Todas (6)' }).click();
    await page.locator('.desktop-table').getByRole('button', { name: 'Editar' }).first().click();
    await page.setViewportSize(viewport);
    const editor = page.getByRole('dialog', { name: 'Editar credencial' });
    const save = editor.getByRole('button', { name: 'Guardar cambios' });
    await page.route('**/api/records/*', route => route.fulfill({
      status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Error largo. '.repeat(100) }),
    }), { times: 1 });
    await save.click();
    await expect(editor.getByRole('alert')).toBeVisible();
    const url = editor.getByLabel('URL o paquete Android');
    await url.scrollIntoViewIfNeeded();
    expect(await url.evaluate(element => {
      const box = element.getBoundingClientRect();
      return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
    })).toBe(true);
    await url.click();
    await url.fill('https://edited.invalid/');
    await save.click();
    await expect(editor).toHaveCount(0);
  });
}
