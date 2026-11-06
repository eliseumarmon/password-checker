import { expect, test, type Page } from '@playwright/test';
import {
  bodyRows, column, currentPage, desktopTable, goToPage, pageButtons, pageControl, sortBy,
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
