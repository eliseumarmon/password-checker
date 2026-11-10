import { expect, test, type Page } from '@playwright/test';
import {
  cardNames, CHROMIUM_HEADER, chromiumRow, column, columnHeader, currentPage, desktopTable, goToPage, numberedRows, seed,
  showAllRecords, sortBy,
} from './tables';

// Review filters and order (review-filters). Fictional credentials only, built in memory.

// The tables compare text with the browser's locale, so the expected orders hold for this one.
test.use({ locale: 'es-ES' });

type Review = 'pending' | 'reviewed' | 'verified' | 'incorrect';

// Four records on their own and two groups: «Grupo Uno» mixes states, «Grupo Dos» has only one.
const STATES: [name: string, username: string, review: Review][] = [
  ['Alfa', 'alfa', 'pending'], ['Bravo', 'bravo', 'reviewed'], ['Charlie', 'charlie', 'verified'], ['Delta', 'delta', 'incorrect'],
  ['Grupo Uno', 'uno-a', 'verified'], ['Grupo Uno', 'uno-b', 'pending'],
  ['Grupo Dos', 'dos-a', 'reviewed'], ['Grupo Dos', 'dos-b', 'reviewed'],
];

async function seedReviewed(page: Page): Promise<void> {
  await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...STATES.map(([name, username]) => chromiumRow(name, username))] }]);
  const { records } = await (await page.request.get('/api/workspace')).json() as { records: { id: string; name: string; username: string }[] };
  for (const [name, username, review] of STATES) {
    if (review === 'pending') continue;
    const id = records.find(r => r.name === name && r.username === username)!.id;
    expect((await page.request.patch(`/api/records/${encodeURIComponent(id)}`, { data: { review } })).ok()).toBe(true);
  }
  await page.reload();
}

function reviewFilter(page: Page) {
  return page.getByRole('combobox', { name: 'Filtrar estado' });
}

test('filters by review state with a selector that replaces the pending-only checkbox', async ({ page }) => {
  await seedReviewed(page);
  await expect(reviewFilter(page).locator('option')).toHaveText(['Todos los estados', 'Pendiente', 'Revisada', 'Verificada', 'No funciona']);
  await expect(reviewFilter(page)).toHaveValue('all');
  await expect(page.getByRole('checkbox', { name: 'Solo pendientes' })).toHaveCount(0);
});

test('shows in «Todas» only the records in the chosen state', async ({ page }) => {
  await seedReviewed(page);
  await showAllRecords(page, STATES.length);
  const users = column(desktopTable(page), 2);
  const expected: [label: string, users: string[]][] = [
    ['Pendiente', ['alfa', 'uno-b']],
    ['Revisada', ['bravo', 'dos-a', 'dos-b']],
    ['Verificada', ['charlie', 'uno-a']],
    ['No funciona', ['delta']],
    ['Todos los estados', ['alfa', 'bravo', 'charlie', 'delta', 'dos-a', 'dos-b', 'uno-a', 'uno-b']],
  ];
  for (const [label, shown] of expected) {
    await reviewFilter(page).selectOption({ label });
    await expect(users).toHaveText(shown);
  }
});

test('keeps in «Duplicados» the groups with a member in the chosen state', async ({ page }) => {
  await seedReviewed(page);
  const names = column(desktopTable(page), 1);
  const expected: [label: string, groups: string[]][] = [
    ['Pendiente', ['Grupo Uno']],
    ['Revisada', ['Grupo Dos']],
    ['Verificada', ['Grupo Uno']],
    ['Todos los estados', ['Grupo Dos', 'Grupo Uno']],
  ];
  for (const [label, shown] of expected) {
    await reviewFilter(page).selectOption({ label });
    await expect(names).toHaveText(shown);
  }
  await reviewFilter(page).selectOption({ label: 'No funciona' });
  await expect(page.getByText('No hay grupos que coincidan con los filtros.')).toBeVisible();
});

function orderSelect(page: Page) {
  return page.getByRole('combobox', { name: 'Ordenar' });
}

function chosenOrder(page: Page) {
  return orderSelect(page).locator('option:checked');
}

const RECORD_ORDERS = [
  'Sitio / App (ascendente)', 'Sitio / App (descendente)', 'Usuario (ascendente)', 'Usuario (descendente)',
  'Tipo (ascendente)', 'Tipo (descendente)', 'Origen (ascendente)', 'Origen (descendente)',
  'Revisión (ascendente)', 'Revisión (descendente)', 'Orden de importación',
];
const GROUP_ORDERS = [
  'Sitio (ascendente)', 'Sitio (descendente)', 'Usuario (ascendente)', 'Usuario (descendente)',
  'Tipo (ascendente)', 'Tipo (descendente)', 'Copias (ascendente)', 'Copias (descendente)',
  'Comparación (ascendente)', 'Comparación (descendente)', 'Contraseñas diferentes primero',
];
// Imported in an order that is neither by name nor by user.
const THREE = [CHROMIUM_HEADER, chromiumRow('Charlie', 'carol'), chromiumRow('Alpha', 'dave'), chromiumRow('Bravo', 'bob')];

test.describe('one order per table', () => {
  test('offers every column of the table on screen, in both directions', async ({ page }) => {
    await seedReviewed(page);
    await expect(orderSelect(page).locator('option')).toHaveText(GROUP_ORDERS);
    await expect(chosenOrder(page)).toHaveText('Sitio (ascendente)');
    await showAllRecords(page, STATES.length);
    await expect(orderSelect(page).locator('option')).toHaveText(RECORD_ORDERS);
    await expect(chosenOrder(page)).toHaveText('Sitio / App (ascendente)');
  });

  test('sorts the table from the selector and marks the column header', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    await showAllRecords(page, 3);
    const table = desktopTable(page);
    await orderSelect(page).selectOption({ label: 'Usuario (descendente)' });
    await expect(column(table, 2)).toHaveText(['dave', 'carol', 'bob']);
    await expect(columnHeader(table, 'Usuario')).toHaveAttribute('aria-sort', 'descending');
    await expect(table.locator('th[aria-sort]')).toHaveCount(1);
    await orderSelect(page).selectOption({ label: 'Orden de importación' });
    await expect(column(table, 1)).toHaveText(['Charlie', 'Alpha', 'Bravo']);
    await expect(table.locator('th[aria-sort]')).toHaveCount(0);
  });

  test('shows in the selector the order set from a column header', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    await showAllRecords(page, 3);
    const table = desktopTable(page);
    await sortBy(table, 'Usuario');
    await expect(chosenOrder(page)).toHaveText('Usuario (ascendente)');
    await sortBy(table, 'Usuario');
    await expect(chosenOrder(page)).toHaveText('Usuario (descendente)');
    await sortBy(table, 'Usuario');
    await expect(chosenOrder(page)).toHaveText('Orden de importación');
  });

  test('keeps the order of each table apart', async ({ page }) => {
    await seedReviewed(page);
    await orderSelect(page).selectOption({ label: 'Copias (descendente)' });
    await showAllRecords(page, STATES.length);
    await expect(chosenOrder(page)).toHaveText('Sitio / App (ascendente)');
    await orderSelect(page).selectOption({ label: 'Usuario (descendente)' });
    await page.getByRole('tab', { name: /^Duplicados/ }).click();
    await expect(chosenOrder(page)).toHaveText('Copias (descendente)');
    await showAllRecords(page, STATES.length);
    await expect(chosenOrder(page)).toHaveText('Usuario (descendente)');
  });

  test('returns to the first page when the order changes from the selector', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: [CHROMIUM_HEADER, ...numberedRows('Alpha', 60), ...numberedRows('Beta', 35)] }]);
    await showAllRecords(page, 95);
    const table = desktopTable(page);
    await goToPage(table, 3);
    await expect(currentPage(table)).toHaveText('3');
    await orderSelect(page).selectOption({ label: 'Usuario (descendente)' });
    await expect(currentPage(table)).toHaveText('1');
    await expect(column(table, 2).first()).toHaveText('beta-34');
  });
});

test.describe('on a phone', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test('lists the record cards in the order of their table', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    await showAllRecords(page, 3);
    await expect(cardNames(page)).toHaveText(['Alpha', 'Bravo', 'Charlie']);
    await orderSelect(page).selectOption({ label: 'Usuario (descendente)' });
    await expect(cardNames(page)).toHaveText(['Alpha', 'Charlie', 'Bravo']);
  });

  test('lists the group cards in the order of their table', async ({ page }) => {
    // The server sends «Zeta» first, because groups with different passwords come first.
    await seed(page, [{ name: 'chrome.csv', lines: [
      CHROMIUM_HEADER, chromiumRow('Alfa', 'alfa-1'), chromiumRow('Alfa', 'alfa-2'),
      'Zeta,https://zeta.invalid/,zeta,fake-zeta-secret-1,', 'Zeta,https://zeta.invalid/,zeta,fake-zeta-secret-2,',
    ] }]);
    await expect(cardNames(page)).toHaveText(['Alfa', 'Zeta']);
    await orderSelect(page).selectOption({ label: 'Contraseñas diferentes primero' });
    await expect(cardNames(page)).toHaveText(['Zeta', 'Alfa']);
  });

  test('lists the trash cards in the order of its table', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    const ids = (await (await page.request.get('/api/workspace')).json()).records.map((record: { id: string }) => record.id);
    expect((await page.request.post('/api/records/trash', { data: { ids } })).ok()).toBe(true);
    await page.reload();
    await page.getByRole('navigation', { name: 'Navegación móvil' }).getByRole('button', { name: /Papelera/ }).click();
    await expect(cardNames(page)).toHaveText(['Alpha', 'Bravo', 'Charlie']);
  });
});

for (const width of [320, 390]) {
  test(`keeps every filter control inside the panel at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 800 });
    await seedReviewed(page);
    const panel = (await page.getByRole('tabpanel').boundingBox())!;
    const controls = page.getByRole('tabpanel').locator('.filters').locator('input, select');
    await expect(controls).toHaveCount(4);
    for (const control of await controls.all()) {
      const box = (await control.boundingBox())!;
      expect(box.x).toBeGreaterThanOrEqual(panel.x);
      expect(box.x + box.width).toBeLessThanOrEqual(panel.x + panel.width);
    }
  });
}
