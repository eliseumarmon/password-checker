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

  const alert = page.getByRole('alert');
  await expect(alert).toContainText('No se pudo guardar la sesión (503)');
  await expect(alert).not.toContainText(passphrase);
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
