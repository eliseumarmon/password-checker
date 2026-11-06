import { expect, test, type Page } from '@playwright/test';
import {
  bodyRows, column, columnHeader, currentPage, desktopTable, goToPage, pageButtons, pageControl, sortBy,
} from './tables';

// Characterization of the desktop tables (native-tables T1): these tests pin how sorting and
// paging behave today, so the native tables can be checked against the same expectations.
// Fictional credentials only, built in memory.

const CHROMIUM_HEADER = 'name,url,username,password,note';

// The tables compare text with the browser's locale, so the expected orders hold for this one.
test.use({ locale: 'es-ES' });

interface CsvFile { name: string; lines: string[] }

/** Replaces the shared E2E workspace with these files and opens the app.
 * Safe only because the E2E tests run serially against one backend (playwright.config.ts). */
async function seed(page: Page, files: CsvFile[]): Promise<void> {
  const form = new FormData();
  for (const file of files) form.append('files', new Blob([file.lines.join('\n')], { type: 'text/csv' }), file.name);
  const imported = await page.request.post('/api/import', { multipart: form });
  expect(imported.ok()).toBe(true);
  await page.goto('/');
}

function chromiumRow(name: string, username: string): string {
  const slug = name.normalize('NFD').replace(/[^\w]+/g, '-').toLowerCase();
  return `${name},https://${slug}.invalid/,${username},fake-${slug}-secret-1234,`;
}

/** `count` sites named "<prefix> 00", "<prefix> 01"… with user names "<prefix>-00"… */
function numberedRows(prefix: string, count: number): string[] {
  return Array.from({ length: count }, (_, index) => {
    const number = String(index).padStart(2, '0');
    return chromiumRow(`${prefix} ${number}`, `${prefix.toLowerCase()}-${number}`);
  });
}

async function showAllRecords(page: Page, count: number): Promise<void> {
  await page.getByRole('button', { name: `Todas (${count})` }).click();
}

test('sorts by name at first, comparing numbers, case and accents as a person reads them', async ({ page }) => {
  const names = ['zulu', 'a10', 'Beta', 'Álamo', 'a2', 'beta', 'alpha', 'Zeta'];
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...names.map((name, i) => chromiumRow(name, `user-${i}`))] }]);
  await showAllRecords(page, names.length);
  await expect(column(desktopTable(page), 1)).toHaveText(['a2', 'a10', 'Álamo', 'alpha', 'beta', 'Beta', 'Zeta', 'zulu']);
});

test('cycles a column through ascending, descending and the original order', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [
    CHROMIUM_HEADER, chromiumRow('Charlie', 'carol'), chromiumRow('Alpha', 'dave'), chromiumRow('Bravo', 'bob'),
  ] }]);
  await showAllRecords(page, 3);
  const table = desktopTable(page);
  await sortBy(table, 'Usuario');
  await expect(column(table, 2)).toHaveText(['bob', 'carol', 'dave']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 2)).toHaveText(['dave', 'carol', 'bob']);
  await sortBy(table, 'Usuario');
  // Unsorted means the order the records arrive in, not the initial sort by name.
  await expect(column(table, 1)).toHaveText(['Charlie', 'Alpha', 'Bravo']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 2)).toHaveText(['bob', 'carol', 'dave']);
});

test('keeps tied rows in their original order in both directions', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [
    CHROMIUM_HEADER, chromiumRow('Charlie', 'same'), chromiumRow('Alpha', 'other'), chromiumRow('Bravo', 'same'),
  ] }]);
  await showAllRecords(page, 3);
  const table = desktopTable(page);
  await sortBy(table, 'Usuario');
  await expect(column(table, 1)).toHaveText(['Alpha', 'Charlie', 'Bravo']);
  // Descending is not the ascending order reversed: the tied rows keep their original order.
  await sortBy(table, 'Usuario');
  await expect(column(table, 1)).toHaveText(['Charlie', 'Bravo', 'Alpha']);
});

test('sorts the number of copies as numbers', async ({ page }) => {
  const copies = (name: string, count: number) => Array.from({ length: count }, () => chromiumRow(name, 'alice'));
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...copies('Bravo', 10), ...copies('Charlie', 2), ...copies('Alpha', 3)] }]);
  const table = desktopTable(page);
  await sortBy(table, 'Copias');
  await expect(column(table, 4)).toHaveText(['2', '3', '10']);
  await sortBy(table, 'Copias');
  await expect(column(table, 4)).toHaveText(['10', '3', '2']);
  await sortBy(table, 'Copias');
  // The groups arrive ordered by name, so the original order is neither of the other two.
  await expect(column(table, 4)).toHaveText(['3', '10', '2']);
});

test('keeps empty values last in both directions', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [
    CHROMIUM_HEADER, chromiumRow('Bravo', 'bob'), chromiumRow('Empty', ''), chromiumRow('Alpha', 'alice'),
  ] }]);
  await showAllRecords(page, 3);
  const table = desktopTable(page);
  await sortBy(table, 'Usuario');
  await expect(column(table, 1)).toHaveText(['Alpha', 'Bravo', 'Empty']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 1)).toHaveText(['Bravo', 'Alpha', 'Empty']);
});

test('sorts the trash table like the others', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [
    CHROMIUM_HEADER, chromiumRow('Charlie', 'carol'), chromiumRow('Alpha', 'dave'), chromiumRow('Bravo', 'bob'),
  ] }]);
  const ids = (await (await page.request.get('/api/workspace')).json()).records.map((record: { id: string }) => record.id);
  expect((await page.request.post('/api/records/trash', { data: { ids } })).ok()).toBe(true);
  await page.reload();
  await page.getByRole('button', { name: 'Papelera (3)' }).first().click();
  const table = desktopTable(page);
  await expect(column(table, 1)).toHaveText(['Alpha', 'Bravo', 'Charlie']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 2)).toHaveText(['bob', 'carol', 'dave']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 2)).toHaveText(['dave', 'carol', 'bob']);
  await sortBy(table, 'Usuario');
  await expect(column(table, 1)).toHaveText(['Charlie', 'Alpha', 'Bravo']);
});

test('sorts by the stored value, not by the label it shows', async ({ page }) => {
  await seed(page, [
    { name: 'brave.csv', lines: [CHROMIUM_HEADER, chromiumRow('Brave site', 'bravo')] },
    { name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Chrome site', 'charlie')] },
    { name: 'firefox.csv', lines: ['url,username,password,httpRealm', 'https://firefox-site.invalid/,foxtrot,fake-firefox-secret-1234,'] },
    { name: 'export.csv', lines: ['url,username,password', 'https://generic-site.invalid/,golf,fake-generic-secret-1234'] },
  ]);
  await showAllRecords(page, 4);
  const table = desktopTable(page);
  await sortBy(table, 'Origen');
  // "unknown" sorts last although its label, «Desconocido», would sort before «firefox».
  await expect(column(table, 4)).toHaveText(['brave', 'chrome', 'firefox', 'Desconocido']);
});

test.describe('paging', () => {
  const ROWS = [CHROMIUM_HEADER, ...numberedRows('Alpha', 60), ...numberedRows('Beta', 35)];

  test.beforeEach(async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: ROWS }]);
    await showAllRecords(page, 95);
  });

  test('moves between pages with every paginator control', async ({ page }) => {
    const table = desktopTable(page);
    const firstName = column(table, 1).first();
    await expect(pageButtons(table)).toHaveText(['1', '2', '3', '4']);
    await expect(currentPage(table)).toHaveText('1');
    await expect(pageControl(table, 'first')).toBeDisabled();
    await expect(pageControl(table, 'previous')).toBeDisabled();

    await goToPage(table, 'next');
    await expect(currentPage(table)).toHaveText('2');
    await expect(firstName).toHaveText('Alpha 30');
    await goToPage(table, 'last');
    await expect(currentPage(table)).toHaveText('4');
    await expect(bodyRows(table)).toHaveCount(5);
    await expect(firstName).toHaveText('Beta 30');
    await expect(pageControl(table, 'next')).toBeDisabled();
    await expect(pageControl(table, 'last')).toBeDisabled();
    await goToPage(table, 'previous');
    await expect(currentPage(table)).toHaveText('3');
    await expect(firstName).toHaveText('Beta 00');
    await goToPage(table, 'first');
    await expect(currentPage(table)).toHaveText('1');
    await expect(firstName).toHaveText('Alpha 00');
    await goToPage(table, 3);
    await expect(currentPage(table)).toHaveText('3');
  });

  test('returns to the first page when the sort changes', async ({ page }) => {
    const table = desktopTable(page);
    await goToPage(table, 3);
    await expect(currentPage(table)).toHaveText('3');
    await sortBy(table, 'Usuario');
    await expect(currentPage(table)).toHaveText('1');
    await expect(column(table, 2).first()).toHaveText('alpha-00');
  });

  test('moves to the last page that still exists when a filter leaves fewer pages', async ({ page }) => {
    const table = desktopTable(page);
    const search = page.getByRole('textbox', { name: 'Buscar credenciales' });
    await goToPage(table, 4);
    await expect(currentPage(table)).toHaveText('4');
    await search.fill('Beta');
    await expect(currentPage(table)).toHaveText('2');
    await expect(bodyRows(table)).toHaveCount(5);
    await search.fill('');
    await expect(bodyRows(table)).toHaveCount(30);
    await expect(currentPage(table)).toHaveText('2');

    await search.fill('Alpha');
    await expect(column(table, 1).first()).toHaveText('Alpha 30');
    await expect(currentPage(table)).toHaveText('2');
  });
});

test('shows at most five page numbers around the current page', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Alpha', 99), ...numberedRows('Beta', 76)] }]);
  await showAllRecords(page, 175);
  const table = desktopTable(page);
  await expect(pageButtons(table)).toHaveText(['1', '2', '3', '4', '5']);
  await goToPage(table, 'last');
  await expect(currentPage(table)).toHaveText('6');
  await expect(pageButtons(table)).toHaveText(['2', '3', '4', '5', '6']);
  await goToPage(table, 'first');
  await expect(pageButtons(table)).toHaveText(['1', '2', '3', '4', '5']);
  await goToPage(table, 3);
  await expect(pageButtons(table)).toHaveText(['1', '2', '3', '4', '5']);
  await goToPage(table, 4);
  await expect(currentPage(table)).toHaveText('4');
  await expect(pageButtons(table)).toHaveText(['2', '3', '4', '5', '6']);
});

test('moves to the previous page when the last one empties', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Alpha', 61)] }]);
  await showAllRecords(page, 61);
  const table = desktopTable(page);
  await goToPage(table, 'last');
  await expect(currentPage(table)).toHaveText('3');
  await bodyRows(table).getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(page.getByRole('button', { name: 'Todas (60)' })).toBeVisible();
  await expect(currentPage(table)).toHaveText('2');
  await expect(column(table, 1).first()).toHaveText('Alpha 30');
});

test('scrolls a wide table inside itself instead of widening the page', async ({ page }) => {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Alpha', `user-${'x'.repeat(120)}`)] }]);
  await page.setViewportSize({ width: 900, height: 720 });
  await showAllRecords(page, 1);
  await expect(desktopTable(page)).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBe(0);
});

// Accessibility of the native tables (native-tables S3): semantics, keyboard and focus.
test.describe('accessible records table', () => {
  test('marks only the sorted column with aria-sort', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Bravo', 'bob'), chromiumRow('Alpha', 'alice')] }]);
    await showAllRecords(page, 2);
    const table = desktopTable(page);
    const sorted = table.locator('thead th[aria-sort]');
    await expect(sorted).toHaveCount(1);
    await expect(columnHeader(table, 'Sitio / App')).toHaveAttribute('aria-sort', 'ascending');
    await sortBy(table, 'Usuario');
    await expect(sorted).toHaveCount(1);
    await expect(columnHeader(table, 'Usuario')).toHaveAttribute('aria-sort', 'ascending');
    await sortBy(table, 'Usuario');
    await expect(columnHeader(table, 'Usuario')).toHaveAttribute('aria-sort', 'descending');
    await sortBy(table, 'Usuario');
    await expect(sorted).toHaveCount(0);
  });

  test('sorts from the keyboard and keeps focus on the header button', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Bravo', 'bob'), chromiumRow('Alpha', 'carol')] }]);
    await showAllRecords(page, 2);
    const table = desktopTable(page);
    const button = columnHeader(table, 'Usuario').getByRole('button', { name: 'Usuario', exact: true });
    await button.focus();
    await page.keyboard.press('Enter');
    await expect(column(table, 2)).toHaveText(['bob', 'carol']);
    await expect(button).toBeFocused();
    await page.keyboard.press('Space');
    await expect(column(table, 2)).toHaveText(['carol', 'bob']);
    await expect(button).toBeFocused();
  });

  test('names the paginator and its controls in Spanish and marks the current page', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Alpha', 95)] }]);
    await showAllRecords(page, 95);
    const nav = desktopTable(page).getByRole('navigation', { name: 'Paginación' });
    for (const name of ['Primera página', 'Página anterior', 'Página 1', 'Página 2', 'Página 3', 'Página 4', 'Página siguiente', 'Última página']) {
      await expect(nav.getByRole('button', { name, exact: true })).toBeVisible();
    }
    await expect(nav.getByRole('button', { name: 'Página 1', exact: true })).toHaveAttribute('aria-current', 'page');
    await expect(nav.locator('[aria-current]')).toHaveCount(1);
  });

  test('keeps focus in the paginator when the control used becomes disabled', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Alpha', 95)] }]);
    await showAllRecords(page, 95);
    const nav = desktopTable(page).getByRole('navigation', { name: 'Paginación' });
    const control = (name: string) => nav.getByRole('button', { name, exact: true });
    await control('Última página').focus();
    await page.keyboard.press('Enter');
    await expect(control('Página 4')).toHaveAttribute('aria-current', 'page');
    await expect(control('Página 4')).toBeFocused();
    await control('Página anterior').focus();
    await page.keyboard.press('Enter');
    await expect(control('Página 3')).toHaveAttribute('aria-current', 'page');
    await expect(control('Página anterior')).toBeFocused();
    await control('Primera página').focus();
    await page.keyboard.press('Enter');
    await expect(control('Página 1')).toBeFocused();
  });

  test('moves focus to a neighbouring row, or to the section title, after moving a row to the trash', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [
      CHROMIUM_HEADER, chromiumRow('Alpha', 'alice'), chromiumRow('Bravo', 'bob'), chromiumRow('Charlie', 'carol'),
    ] }]);
    await showAllRecords(page, 3);
    const trashOf = (name: string) => desktopTable(page).getByRole('row', { name: new RegExp(name) })
      .getByRole('button', { name: 'Mover a la papelera' });
    await trashOf('Bravo').focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('button', { name: 'Todas (2)' })).toBeVisible();
    await expect(trashOf('Charlie')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('button', { name: 'Todas (1)' })).toBeVisible();
    await expect(trashOf('Alpha')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('button', { name: 'Todas (0)' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Explorar y consolidar' })).toBeFocused();
  });
});

test.describe('accessible groups and trash tables', () => {
  test('sorts groups from the keyboard and moves focus after moving a group to the trash', async ({ page }) => {
    const copies = (name: string, count: number) => Array.from({ length: count }, () => chromiumRow(name, 'alice'));
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...copies('Alpha', 2), ...copies('Bravo', 3), ...copies('Charlie', 2)] }]);
    const table = desktopTable(page);
    await expect(columnHeader(table, 'Sitio')).toHaveAttribute('aria-sort', 'ascending');
    const copiesButton = columnHeader(table, 'Copias').getByRole('button', { name: 'Copias', exact: true });
    await copiesButton.focus();
    await page.keyboard.press('Enter');
    await expect(columnHeader(table, 'Copias')).toHaveAttribute('aria-sort', 'ascending');
    await expect(copiesButton).toBeFocused();
    await expect(column(table, 1)).toHaveText(['Alpha', 'Charlie', 'Bravo']);

    const trashOf = (name: string) => table.getByRole('row', { name: new RegExp(name) })
      .getByRole('button', { name: 'Mover grupo a la papelera' });
    await trashOf('Charlie').focus();
    await page.keyboard.press('Enter');
    await page.getByRole('alertdialog', { name: 'Confirmar acción' }).getByRole('button', { name: 'Mover a la papelera', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Duplicados (2)' })).toBeVisible();
    await expect(trashOf('Bravo')).toBeFocused();
  });

  test('leaves focus alone when a cancelled removal is followed by a filter that hides the row', async ({ page }) => {
    const copies = (name: string) => [chromiumRow(name, 'alice'), chromiumRow(name, 'alice')];
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...copies('Alpha'), ...copies('Bravo')] }]);
    await desktopTable(page).getByRole('row', { name: /Alpha/ }).getByRole('button', { name: 'Mover grupo a la papelera' }).click();
    await page.getByRole('alertdialog', { name: 'Confirmar acción' }).getByRole('button', { name: 'Cancelar' }).click();
    const search = page.getByRole('textbox', { name: 'Buscar credenciales' });
    await search.click();
    await page.keyboard.type('Bravo');
    await expect(column(desktopTable(page), 1)).toHaveText(['Bravo']);
    await expect(search).toBeFocused();
    await expect(search).toHaveValue('Bravo');
  });

  test('restores from the keyboard and moves focus to a neighbouring row or to the trash title', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, chromiumRow('Alpha', 'alice'), chromiumRow('Bravo', 'bob')] }]);
    const ids = (await (await page.request.get('/api/workspace')).json()).records.map((record: { id: string }) => record.id);
    expect((await page.request.post('/api/records/trash', { data: { ids } })).ok()).toBe(true);
    await page.reload();
    await page.getByRole('button', { name: 'Papelera (2)' }).first().click();
    const table = desktopTable(page);
    await expect(table.getByRole('table', { name: 'Credenciales descartadas' })).toBeVisible();
    const restoreOf = (name: string) => table.getByRole('row', { name: new RegExp(name) }).getByRole('button', { name: 'Restaurar' });
    await restoreOf('Alpha').focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('button', { name: 'Papelera (1)' }).first()).toBeVisible();
    await expect(restoreOf('Bravo')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByText('La papelera está vacía.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Credenciales descartadas' })).toBeFocused();
  });
});
