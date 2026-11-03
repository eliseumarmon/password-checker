import { expect, test, type Locator, type Page } from '@playwright/test';

// Fictional credentials only, built in memory: real exports never touch the repo.
const TWO_COLUMN_CSV = [
  'url,username,password,extra_secret,backup_code',
  'https://alpha.invalid/,alice,fake-Alpha-123,fake-secret-value-1,fake-code-1',
  'https://beta.invalid/,bob,fake-Beta-456,,fake-code-2',
  'https://alpha.invalid/,alice,fake-Alpha-123,fake-secret-value-3,',
].join('\n');
const CLEAN_CSV = 'url,username,password\nhttps://clean.invalid/,dan,fake-Clean-789\n';
const ONE_COLUMN_CSV = [
  'url,username,password,token',
  'https://other.invalid/,erin,fake-Other-321,fake-token-value',
].join('\n');
const THREE_COLUMN_CSV = [
  'url,username,password,c1,c2,c3',
  'https://three.invalid/,frank,fake-Three-111,v1,v2,v3',
].join('\n');
const FOUR_COLUMN_CSV = [
  'url,username,password,columna_larga_uno,columna_larga_dos,columna_larga_tres,columna_larga_cuatro',
  'https://four.invalid/,grace,fake-Four-222,v1,v2,v3,v4',
].join('\n');
const TWO_FILES_CSV_A = 'url,username,password,d1,d2\nhttps://a.invalid/,heidi,fake-A-1,x,y\n';
const TWO_FILES_CSV_B = 'url,username,password,e1,e2\nhttps://b.invalid/,ivan,fake-B-2,x,y\n';
const ZERO_FIRST_DUP = 'url,username,password,extra\nhttps://dup.invalid/,judy,fake-Dup-1,secret-a\n';
const ZERO_SECOND_DUP = 'url,username,password,pin\n,,,secret-b\n';
const XSS_CSV = [
  'url,username,password,<script>alert(1)</script>',
  'https://xss.invalid/,mallory,fake-Xss-999,fictional-discarded-value',
].join('\n');

function csvFile(name: string, csv: string) {
  return { name, mimeType: 'text/csv', buffer: Buffer.from(csv) };
}

function warning(page: Page): Locator {
  return page.locator('.page-notices .warning');
}

async function importViaUi(page: Page, files: { name: string; mimeType: string; buffer: Buffer }[], action: 'confirm' | 'cancel' = 'confirm'): Promise<void> {
  // The E2E backend is shared between tests, so importing may replace the previous test's data.
  const state = await page.request.get('/api/workspace');
  const replacing = (await state.json()).stats.total > 0;
  // No navigation when already on the app: a reload would clear the in-memory warnings.
  if (new URL(page.url()).pathname !== '/') await page.goto('/');
  await page.locator('input[type=file][accept*=".csv"]').first().setInputFiles(files);
  if (replacing) {
    const dialog = page.getByRole('alertdialog', { name: 'Confirmar acción' });
    await dialog.getByRole('button', { name: action === 'confirm' ? 'Importar' : 'Cancelar', exact: true }).click();
    await expect(dialog).toBeHidden();
  }
}

async function confirmWith(page: Page, label: string): Promise<void> {
  const dialog = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await dialog.getByRole('button', { name: label, exact: true }).click();
  await expect(dialog).toBeHidden();
}

async function exportBitwarden(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  await confirmWith(page, 'Generar CSV');
}

// What really sits at the centre of the notice: the notice itself, or the overlay covering it.
async function topAtWarningCenter(page: Page): Promise<string> {
  const box = (await warning(page).boundingBox())!;
  return page.evaluate(([x, y]) => {
    const element = document.elementFromPoint(x, y);
    if (!element) return 'none';
    if (element.closest('.warning')) return 'warning';
    const overlay = element.closest('.overlay');
    return overlay ? `overlay:${overlay.className}` : `other:${element.tagName}`;
  }, [box.x + box.width / 2, box.y + box.height / 2]);
}

async function isDirectlyClickable(locator: Locator): Promise<boolean> {
  return locator.evaluate(element => {
    const box = element.getBoundingClientRect();
    return document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2) === element;
  });
}

test('shows the import warning with file, columns and row counts, never the discarded values', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  await expect(page.getByRole('button', { name: 'Todas (3)' })).toBeVisible();
  const notice = warning(page);
  await expect(notice).toBeVisible();
  await expect(notice.getByText('Importación completada con advertencias', { exact: true })).toBeVisible();
  await expect(notice).toContainText('Se han importado 3 credenciales de adv.csv');
  await expect(notice).toContainText('extra_secret: 2 filas con datos');
  await expect(notice).toContainText('backup_code: 2 filas con datos');
  await expect(notice).toContainText('Los valores descartados no se incluirán en la exportación.');
  expect(await page.locator('.page-notices').textContent()).not.toContain('fake-secret-value');
  expect(await page.locator('.page-notices').textContent()).not.toContain('fake-code-1');
  // Manual close only: it does not disappear on its own.
  await page.waitForTimeout(1500);
  await expect(notice).toBeVisible();
  await notice.getByRole('button', { name: 'Cerrar aviso' }).click();
  await expect(notice).toHaveCount(0);
});

test('keeps the warning across screens, dialogs, edits and undo', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  const sidebar = page.getByRole('complementary', { name: 'Navegación principal' });
  for (const name of [/Auditoría/, /Papelera/, /Ajustes/]) {
    await sidebar.getByRole('button', { name }).click();
    await expect(notice).toBeVisible();
  }
  await sidebar.getByRole('button', { name: /Credenciales/ }).click();
  await page.getByRole('button', { name: 'Todas (3)' }).click();
  // Behind the editor, then back on top once it closes.
  await page.locator('.desktop-table').getByRole('row', { name: /alice/ }).first().getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor).toBeVisible();
  await expect(notice).toHaveCount(1);
  expect(await topAtWarningCenter(page)).toContain('overlay');
  await editor.getByLabel('Nombre').fill('Alice editada');
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(editor).toBeHidden();
  await expect(notice).toBeVisible();
  await expect(page.locator('.desktop-table')).toContainText('Alice editada');
  expect(await topAtWarningCenter(page)).toBe('warning');
  await page.getByRole('button', { name: /Deshacer/ }).click();
  // Undo is async: wait until the edit is really reverted before checking the warning.
  await expect(page.locator('.desktop-table')).not.toContainText('Alice editada');
  // Both original alpha rows are back, named after the site again (the fixture has no name column).
  await expect(page.locator('.desktop-table').getByRole('row', { name: /^alpha\.invalid/ })).toHaveCount(2);
  await expect(notice).toBeVisible();
});

test('stacks a later error above the warning and both close independently', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  await page.route('**/api/export', route => route.fulfill({ status: 503, body: '' }));
  await exportBitwarden(page);
  const alert = page.getByRole('alert');
  await expect(alert).toContainText('No se pudo exportar');
  await expect(notice).toBeVisible();
  const alertBox = (await alert.boundingBox())!;
  const noticeBox = (await notice.boundingBox())!;
  // The error sits on top, without overlapping the warning.
  expect(alertBox.y + alertBox.height).toBeLessThanOrEqual(noticeBox.y + 1);
  const closeError = alert.getByRole('button', { name: 'Cerrar aviso' });
  const closeWarning = notice.getByRole('button', { name: 'Cerrar aviso' });
  expect(await isDirectlyClickable(closeError)).toBe(true);
  expect(await isDirectlyClickable(closeWarning)).toBe(true);
  await closeError.click();
  await expect(alert).toHaveCount(0);
  await expect(notice).toBeVisible();
  await closeWarning.click();
  await expect(notice).toHaveCount(0);
  await expect(page.locator('.page-notices')).toHaveCount(0);
});

test('keeps the previous warning when a new import is cancelled', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toContainText('adv.csv');
  await importViaUi(page, [csvFile('clean.csv', CLEAN_CSV)], 'cancel');
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('Se han importado 3 credenciales de adv.csv');
  await expect(page.getByRole('button', { name: 'Todas (3)' })).toBeVisible();
});

test('keeps the previous warning when a new import fails', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toContainText('adv.csv');
  await page.route('**/api/import', route => route.fulfill({
    status: 422, contentType: 'application/json', body: JSON.stringify({ detail: 'Fallo ficticio de importación' }),
  }), { times: 1 });
  await importViaUi(page, [csvFile('other.csv', ONE_COLUMN_CSV)]);
  await expect(page.getByRole('alert')).toContainText('Fallo ficticio de importación');
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('extra_secret: 2 filas con datos');
});

test('replaces the warnings on a successful import and clears them on a clean one', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toContainText('extra_secret');
  await importViaUi(page, [csvFile('other.csv', ONE_COLUMN_CSV)]);
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('Se han importado 1 credenciales de other.csv');
  await expect(notice).toContainText('token: 1 fila con datos');
  await expect(notice).not.toContainText('extra_secret');
  await importViaUi(page, [csvFile('clean.csv', CLEAN_CSV)]);
  await expect(notice).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Todas (1)' })).toBeVisible();
});

test('keeps the previous warning while the new import request is still in flight', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toContainText('adv.csv');
  // Real fictional backend data, only held back so the pending state is observable.
  await page.route('**/api/import', async route => {
    const response = await route.fetch();
    await new Promise(resolve => setTimeout(resolve, 1500));
    await route.fulfill({ response });
  });
  await importViaUi(page, [csvFile('clean.csv', CLEAN_CSV)]);
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('adv.csv');
  // The confirmed clean import completes and removes the warnings.
  await expect(notice).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Todas (1)' })).toBeVisible();
});

test('lists up to three discarded columns directly and summarizes from four, across files', async ({ page }) => {
  await importViaUi(page, [csvFile('three.csv', THREE_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('c1: 1 fila con datos');
  await expect(notice).toContainText('c3: 1 fila con datos');
  await expect(notice.getByRole('button', { name: 'Ver detalles' })).toHaveCount(0);
  await expect(notice).not.toContainText('columnas descartadas');

  await importViaUi(page, [csvFile('four.csv', FOUR_COLUMN_CSV)]);
  await expect(notice).toContainText('4 columnas descartadas');
  const toggle = notice.getByRole('button', { name: 'Ver detalles' });
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  const list = notice.locator('ul.warning-files');
  await expect(list).toBeHidden();
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await expect(list).toBeVisible();
  await expect(list).toContainText('columna_larga_cuatro: 1 fila con datos');
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(list).toBeHidden();

  // The threshold counts every column of every file: 2 + 2 = 4, summarized globally.
  await importViaUi(page, [csvFile('a.csv', TWO_FILES_CSV_A), csvFile('b.csv', TWO_FILES_CSV_B)]);
  await expect(notice).toContainText('4 columnas descartadas');
  await notice.getByRole('button', { name: 'Ver detalles' }).click();
  await expect(notice).toContainText('Se han importado 1 credenciales de a.csv');
  await expect(notice).toContainText('Se han importado 1 credenciales de b.csv');
  await expect(notice).toContainText('d1: 1 fila con datos');
  await expect(notice).toContainText('e2: 1 fila con datos');
});

test('collapses the details again for each new import with a summary', async ({ page }) => {
  await importViaUi(page, [csvFile('four.csv', FOUR_COLUMN_CSV)]);
  const notice = warning(page);
  const toggle = notice.getByRole('button', { name: 'Ver detalles' });
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  // The warning stays mounted while the next import replaces it.
  await importViaUi(page, [csvFile('four-again.csv', FOUR_COLUMN_CSV)]);
  await expect(notice.locator('ul.warning-files')).toContainText('four-again.csv');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(notice.locator('ul.warning-files')).toBeHidden();
});

test('stays behind comparison, editor, session and confirmation, and returns when they close', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  expect(await topAtWarningCenter(page)).toBe('warning');

  await page.locator('.desktop-table').getByRole('row', { name: /alpha/ }).getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('dialog', { name: 'Comparar duplicados' });
  await expect(compare).toBeVisible();
  await expect(notice).toHaveCount(1);
  expect(await topAtWarningCenter(page)).toBe('overlay:overlay modal-overlay');
  await compare.getByRole('button', { name: 'Cerrar panel' }).click();
  await expect(compare).toBeHidden();
  expect(await topAtWarningCenter(page)).toBe('warning');

  await page.getByRole('button', { name: 'Todas (3)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /bob/ }).getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor).toBeVisible();
  expect(await topAtWarningCenter(page)).toBe('overlay:overlay modal-overlay');
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  expect(await topAtWarningCenter(page)).toBe('warning');

  await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
  const session = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await expect(session).toBeVisible();
  expect(await topAtWarningCenter(page)).toBe('overlay:overlay modal-overlay');
  await session.getByRole('button', { name: 'Cancelar' }).click();
  expect(await topAtWarningCenter(page)).toBe('warning');

  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  const confirm = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await expect(confirm).toBeVisible();
  expect(await topAtWarningCenter(page)).toBe('overlay:overlay modal-overlay confirm-overlay');
  await confirm.getByRole('button', { name: 'Cancelar' }).click();
  expect(await topAtWarningCenter(page)).toBe('warning');
});

test('renders file and column names as text, never as markup or URLs', async ({ page }) => {
  await importViaUi(page, [csvFile('<img src=x onerror=alert(1)>.csv', XSS_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('<img src=x onerror=alert(1)>.csv');
  await expect(notice).toContainText('<script>alert(1)</script>');
  expect(await page.locator('.warning img, .warning script, .warning iframe, .warning a').count()).toBe(0);
  expect(await page.locator('.page-notices').innerHTML()).not.toContain('<img');
  expect(await page.locator('.page-notices').textContent()).not.toContain('fictional-discarded-value');
});

test('shows zero imported counts and repeated basenames as separate entries', async ({ page }) => {
  await importViaUi(page, [csvFile('dup.csv', ZERO_FIRST_DUP), csvFile('dup.csv', ZERO_SECOND_DUP)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('Se han importado 1 credenciales de dup.csv');
  await expect(notice).toContainText('Se han importado 0 credenciales de dup.csv');
  await expect(notice.locator('ul.warning-files > li')).toHaveCount(2);
  await expect(notice).toContainText('extra: 1 fila con datos');
  await expect(notice).toContainText('pin: 1 fila con datos');
});

test('does not survive a reload and is not stored in the browser', async ({ page }) => {
  await importViaUi(page, [csvFile('adv.csv', TWO_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toBeVisible();
  const storedKeys = await page.evaluate(() => Object.keys(window.localStorage));
  expect(storedKeys.filter(key => key.toLowerCase().includes('warn'))).toEqual([]);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Todas (3)' })).toBeVisible();
  await expect(notice).toHaveCount(0);
  await expect(page.locator('.page-notices')).toHaveCount(0);
});

test('keeps the stacked warning and error usable in a short mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 320 });
  await importViaUi(page, [csvFile('four.csv', FOUR_COLUMN_CSV)]);
  const notice = warning(page);
  await expect(notice).toContainText('4 columnas descartadas');
  await notice.getByRole('button', { name: 'Ver detalles' }).click();
  await expect(notice.locator('ul.warning-files')).toBeVisible();
  await page.route('**/api/export', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Error largo de prueba. '.repeat(100) }),
  }));
  await exportBitwarden(page);
  const alert = page.getByRole('alert');
  await expect(alert).toContainText('Error largo de prueba.');
  const headerBox = (await page.locator('.sticky-head').boundingBox())!;
  const navBox = (await page.getByRole('navigation', { name: 'Navegación móvil' }).boundingBox())!;
  const stack = page.locator('.page-notices');
  const stackBox = (await stack.boundingBox())!;
  expect(stackBox.y).toBeGreaterThanOrEqual(headerBox.y + headerBox.height);
  expect(stackBox.y + stackBox.height).toBeLessThanOrEqual(navBox.y);
  const closeWarning = notice.getByRole('button', { name: 'Cerrar aviso' });
  const closeError = alert.getByRole('button', { name: 'Cerrar aviso' });
  // The error sits on top and is usable without scrolling.
  const alertBox = (await alert.boundingBox())!;
  expect(alertBox.y).toBeGreaterThanOrEqual(headerBox.y + headerBox.height);
  expect(alertBox.y + alertBox.height).toBeLessThanOrEqual(navBox.y);
  expect(await isDirectlyClickable(closeError)).toBe(true);
  // The stacked warning is reached through the single stack scroll; its close button and text scroll stay reachable.
  expect(await stack.evaluate(element => element.scrollHeight > element.clientHeight)).toBe(true);
  await closeWarning.scrollIntoViewIfNeeded();
  const noticeBox = (await notice.boundingBox())!;
  expect(noticeBox.y).toBeGreaterThanOrEqual(headerBox.y + headerBox.height);
  expect(noticeBox.y + noticeBox.height).toBeLessThanOrEqual(navBox.y);
  expect(await isDirectlyClickable(closeWarning)).toBe(true);
  expect(await notice.locator('.notice-text').evaluate(element => element.scrollHeight > element.clientHeight)).toBe(true);
  await closeWarning.focus();
  await page.keyboard.press('Enter');
  await expect(notice).toHaveCount(0);
  await expect(alert).toBeVisible();
  expect(await isDirectlyClickable(closeError)).toBe(true);
  await closeError.click();
  await expect(alert).toHaveCount(0);
});
