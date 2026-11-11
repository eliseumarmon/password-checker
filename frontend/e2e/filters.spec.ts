import { expect, test, type Page } from '@playwright/test';
import {
  bodyRows, cardNames, CHROMIUM_HEADER, chromiumRow, column, columnHeader, currentPage, desktopTable, goToPage, numberedRows, seed,
  showAllRecords, sortBy,
} from './tables';

// Review filters and order (review-filters). Fictional credentials only, built in memory.

// The tables compare text with the browser's locale, so the expected orders hold for this one.
test.use({ locale: 'es-ES' });

type Review = 'pending' | 'reviewed' | 'incorrect';

// Four records on their own and two groups: «Grupo Uno» mixes states, «Grupo Dos» has only one.
const STATES: [name: string, username: string, review: Review][] = [
  ['Alfa', 'alfa', 'pending'], ['Bravo', 'bravo', 'reviewed'], ['Charlie', 'charlie', 'reviewed'], ['Delta', 'delta', 'incorrect'],
  ['Grupo Uno', 'uno-a', 'reviewed'], ['Grupo Uno', 'uno-b', 'pending'],
  ['Grupo Dos', 'dos-a', 'pending'], ['Grupo Dos', 'dos-b', 'pending'],
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
  await expect(reviewFilter(page).locator('option')).toHaveText(['Todos los estados', 'Pendiente', 'Revisada', 'No funciona']);
  await expect(reviewFilter(page)).toHaveValue('all');
  await expect(page.getByRole('checkbox', { name: 'Solo pendientes' })).toHaveCount(0);
});

test('shows in «Todas» only the records in the chosen state', async ({ page }) => {
  await seedReviewed(page);
  await showAllRecords(page, STATES.length);
  const users = column(desktopTable(page), 2);
  const expected: [label: string, users: string[]][] = [
    ['Pendiente', ['alfa', 'dos-a', 'dos-b', 'uno-b']],
    ['Revisada', ['bravo', 'charlie', 'uno-a']],
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
    ['Pendiente', ['Grupo Dos', 'Grupo Uno']],
    ['Revisada', ['Grupo Uno']],
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
  'Revisión (ascendente)', 'Revisión (descendente)',
  'Riesgo (más alertas primero)', 'Riesgo (menos alertas primero)', 'URL (ascendente)', 'URL (descendente)',
  'Orden de importación',
];
const GROUP_ORDERS = [
  'Sitio (ascendente)', 'Sitio (descendente)', 'Usuario (ascendente)', 'Usuario (descendente)',
  'Tipo (ascendente)', 'Tipo (descendente)', 'Copias (ascendente)', 'Copias (descendente)',
  'Comparación (ascendente)', 'Comparación (descendente)', 'Contraseñas diferentes primero',
];
const TRASH_ORDERS = [
  'Sitio / App (ascendente)', 'Sitio / App (descendente)', 'Usuario (ascendente)', 'Usuario (descendente)',
  'Origen (ascendente)', 'Origen (descendente)', 'Orden de importación',
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

  test('lists the trash cards in the order chosen in its own selector', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    const ids = (await (await page.request.get('/api/workspace')).json()).records.map((record: { id: string }) => record.id);
    expect((await page.request.post('/api/records/trash', { data: { ids } })).ok()).toBe(true);
    await page.reload();
    await page.getByRole('navigation', { name: 'Navegación móvil' }).getByRole('button', { name: /Papelera/ }).click();
    await expect(cardNames(page)).toHaveText(['Alpha', 'Bravo', 'Charlie']);
    await expect(orderSelect(page).locator('option')).toHaveText(TRASH_ORDERS);
    await expect(chosenOrder(page)).toHaveText('Sitio / App (ascendente)');
    await orderSelect(page).selectOption({ label: 'Orden de importación' });
    await expect(cardNames(page)).toHaveText(['Charlie', 'Alpha', 'Bravo']);
    await expect(chosenOrder(page)).toHaveText('Orden de importación');
  });
});

for (const width of [320, 390]) {
  test(`keeps every filter control inside the panel at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 800 });
    await seedReviewed(page);
    for (const tab of ['Duplicados', 'Todas']) {
      await page.getByRole('tab', { name: new RegExp(`^${tab}`) }).click();
      const panel = (await page.getByRole('tabpanel').boundingBox())!;
      const controls = page.getByRole('tabpanel').locator('.filters').locator('input, select');
      await expect(controls).toHaveCount(4);
      for (const control of await controls.all()) {
        const box = (await control.boundingBox())!;
        expect(box.x).toBeGreaterThanOrEqual(panel.x);
        expect(box.x + box.width).toBeLessThanOrEqual(panel.x + panel.width);
      }
    }
  });
}

// Alerts as «Auditoría» counts them. Hotel and India share a common password: weak and reused, 2 each.
// Kilo has no user and a common password: incomplete and weak, 2. A record without a user never counts
// as reused, because the server cannot tell whose account it is. Bravo: weak, 1. Delta: no user, 1.
// Alfa and Zulu: none.
const RISK_ROWS = [
  CHROMIUM_HEADER,
  'Zulu,https://zulu.invalid/,zulu,fake-zulu-secret-1234,', 'Kilo,https://kilo.invalid/,,qwerty,',
  'Hotel,https://hotel.invalid/,hotel,abc123,', 'Alfa,https://alfa.invalid/,alfa,fake-alfa-secret-1234,',
  'Delta,https://delta.invalid/,,fake-delta-secret-1234,', 'India,https://india.invalid/,india,abc123,',
  'Bravo,https://bravo.invalid/,bravo,password,',
];

test.describe('risk and URL order in «Todas»', () => {
  test('puts the records with more audit alerts first, and ties by name', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: RISK_ROWS }]);
    await showAllRecords(page, 7);
    const table = desktopTable(page);
    await orderSelect(page).selectOption({ label: 'Riesgo (más alertas primero)' });
    await expect(column(table, 1)).toHaveText(['Hotel', 'India', 'Kilo', 'Bravo', 'Delta', 'Alfa', 'Zulu']);
    await expect(table.locator('th[aria-sort]')).toHaveCount(0);
    await orderSelect(page).selectOption({ label: 'Riesgo (menos alertas primero)' });
    await expect(column(table, 1)).toHaveText(['Alfa', 'Zulu', 'Bravo', 'Delta', 'Hotel', 'India', 'Kilo']);
  });

  test('moves a record as soon as an edit changes its alerts', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: RISK_ROWS }]);
    await showAllRecords(page, 7);
    const table = desktopTable(page);
    await orderSelect(page).selectOption({ label: 'Riesgo (más alertas primero)' });
    await expect(column(table, 1)).toHaveText(['Hotel', 'India', 'Kilo', 'Bravo', 'Delta', 'Alfa', 'Zulu']);
    // A long, unique password takes away Bravo's only alert.
    await bodyRows(table).filter({ hasText: 'Bravo' }).getByRole('button', { name: 'Editar' }).click();
    const editor = page.getByRole('dialog', { name: 'Editar credencial' });
    await editor.getByRole('textbox', { name: /^Contraseña/ }).fill('fake-bravo-secret-1234');
    await editor.getByRole('button', { name: 'Guardar cambios' }).click();
    await expect(editor).toBeHidden();
    await expect(column(table, 1)).toHaveText(['Hotel', 'India', 'Kilo', 'Delta', 'Alfa', 'Bravo', 'Zulu']);
  });

  test('keeps the records of one site together, by host and then by the whole URL', async ({ page }) => {
    // Two records on b.invalid whose names are not next to each other, an Android app, whose host is its
    // package, and a record without a URL, which goes last in both directions.
    await seed(page, [{ name: 'chrome.csv', lines: [
      CHROMIUM_HEADER,
      'Zeta,https://b.invalid/a,zeta,fake-zeta-secret-1234,', 'Alfa,https://a.invalid/z,alfa,fake-alfa-secret-1234,',
      'Mike,https://b.invalid/x,mike,fake-mike-secret-1234,', 'Bravo,android://sig@com.example.app/,bravo,fake-bravo-secret-1234,',
      'Charlie,,charlie,fake-charlie-secret-1234,',
    ] }]);
    await showAllRecords(page, 5);
    const table = desktopTable(page);
    await orderSelect(page).selectOption({ label: 'URL (ascendente)' });
    await expect(column(table, 1)).toHaveText(['Alfa', 'Zeta', 'Mike', 'Bravo', 'Charlie']);
    await orderSelect(page).selectOption({ label: 'URL (descendente)' });
    await expect(column(table, 1)).toHaveText(['Bravo', 'Mike', 'Zeta', 'Alfa', 'Charlie']);
  });

  test('offers the risk and URL orders only in «Todas»', async ({ page }) => {
    await seedReviewed(page);
    await expect(orderSelect(page).locator('option', { hasText: /^(Riesgo|URL) / })).toHaveCount(0);
    await showAllRecords(page, STATES.length);
    await expect(orderSelect(page).locator('option', { hasText: /^(Riesgo|URL) / })).toHaveCount(4);
  });
});

test.describe('after a reload', () => {
  function typeFilter(page: Page) {
    return page.getByRole('combobox', { name: 'Filtrar tipo' });
  }
  function search(page: Page) {
    return page.getByRole('textbox', { name: 'Buscar credenciales' });
  }
  function trashScreen(page: Page) {
    return page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: /Papelera/ });
  }

  test('keeps the type, the state and the order of each table, but not the search', async ({ page }) => {
    await seedReviewed(page);
    const { records } = await (await page.request.get('/api/workspace')).json() as { records: { id: string; name: string }[] };
    const ids = records.filter(r => r.name === 'Delta').map(r => r.id);
    expect((await page.request.post('/api/records/trash', { data: { ids } })).ok()).toBe(true);
    await page.reload();

    await typeFilter(page).selectOption('web');
    await reviewFilter(page).selectOption({ label: 'Revisada' });
    await orderSelect(page).selectOption({ label: 'Copias (descendente)' });
    await showAllRecords(page, STATES.length - 1);
    await orderSelect(page).selectOption({ label: 'Riesgo (más alertas primero)' });
    await search(page).fill('bravo');
    await trashScreen(page).click();
    await orderSelect(page).selectOption({ label: 'Usuario (descendente)' });
    await page.reload();

    await expect(typeFilter(page)).toHaveValue('web');
    await expect(reviewFilter(page)).toHaveValue('reviewed');
    await expect(search(page)).toHaveValue('');
    await expect(chosenOrder(page)).toHaveText('Copias (descendente)');
    await showAllRecords(page, STATES.length - 1);
    await expect(chosenOrder(page)).toHaveText('Riesgo (más alertas primero)');
    await trashScreen(page).click();
    await expect(chosenOrder(page)).toHaveText('Usuario (descendente)');
    // Only view preferences with closed values are stored: no search, name, URL, user or id. The collapsed
    // sidebar key is allowed too, although this flow does not write it.
    const stored = await page.evaluate(() => Object.keys(localStorage).map(key => [key, localStorage.getItem(key) ?? ''] as const));
    const written = ['pc.reviewFilters', 'pc.tableSort.groups', 'pc.tableSort.records', 'pc.tableSort.trash'];
    expect(stored.map(([key]) => key)).toEqual(expect.arrayContaining(written));
    for (const [key, value] of stored) {
      expect([...written, 'pc.sidebarCollapsed']).toContain(key);
      if (key === 'pc.reviewFilters') expect(value).toBe('{"type":"web","review":"reviewed"}');
      else if (key === 'pc.sidebarCollapsed') expect(value).toMatch(/^[01]$/);
      else expect(value).toMatch(/^\{"field":("[a-z]+"|null),"direction":"(ascending|descending)"\}$/);
    }
  });

  test('falls back to the defaults for stored values it does not know', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('pc.reviewFilters', '{"type":"desktop","review":"lost"}');
      // A field that is not one of this table's orders, with a valid direction.
      localStorage.setItem('pc.tableSort.records', '{"field":"password","direction":"ascending"}');
      // A valid field with an unknown direction.
      localStorage.setItem('pc.tableSort.groups', '{"field":"count","direction":"sideways"}');
    });
    await seedReviewed(page);
    await expect(typeFilter(page)).toHaveValue('all');
    await expect(reviewFilter(page)).toHaveValue('all');
    await expect(chosenOrder(page)).toHaveText('Sitio (ascendente)');
    await showAllRecords(page, STATES.length);
    await expect(chosenOrder(page)).toHaveText('Sitio / App (ascendente)');
    await expect(column(desktopTable(page), 2)).toHaveText(['alfa', 'bravo', 'charlie', 'delta', 'dos-a', 'dos-b', 'uno-a', 'uno-b']);
  });

  test('falls back to the defaults for stored values that are not JSON, or another table\'s order', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('pc.reviewFilters', 'not json');
      // «risk» exists only in «Todas».
      localStorage.setItem('pc.tableSort.groups', '{"field":"risk","direction":"descending"}');
      localStorage.setItem('pc.tableSort.records', 'not json');
    });
    await seedReviewed(page);
    await expect(typeFilter(page)).toHaveValue('all');
    await expect(reviewFilter(page)).toHaveValue('all');
    await expect(chosenOrder(page)).toHaveText('Sitio (ascendente)');
    await showAllRecords(page, STATES.length);
    await expect(chosenOrder(page)).toHaveText('Sitio / App (ascendente)');
  });

  test('restores a stored order without sorting', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('pc.tableSort.groups', '{"field":null,"direction":"ascending"}'));
    await seedReviewed(page);
    await expect(chosenOrder(page)).toHaveText('Contraseñas diferentes primero');
    await expect(desktopTable(page).locator('th[aria-sort]')).toHaveCount(0);
  });

  test('keeps an order chosen with a column header', async ({ page }) => {
    await seed(page, [{ name: 'chrome.csv', lines: THREE }]);
    await showAllRecords(page, 3);
    const table = desktopTable(page);
    await sortBy(table, 'Usuario');
    await sortBy(table, 'Usuario');
    await page.reload();
    await showAllRecords(page, 3);
    await expect(chosenOrder(page)).toHaveText('Usuario (descendente)');
    await expect(column(table, 2)).toHaveText(['dave', 'carol', 'bob']);
  });

  test('works the same without browser storage, remembering nothing', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', { configurable: true, get() { throw new DOMException('blocked', 'SecurityError'); } });
    });
    await seedReviewed(page);
    await reviewFilter(page).selectOption({ label: 'Revisada' });
    await expect(column(desktopTable(page), 1)).toHaveText(['Grupo Uno']);
    await orderSelect(page).selectOption({ label: 'Sitio (descendente)' });
    await reviewFilter(page).selectOption({ label: 'Todos los estados' });
    await expect(column(desktopTable(page), 1)).toHaveText(['Grupo Uno', 'Grupo Dos']);
    await page.reload();
    await expect(reviewFilter(page)).toHaveValue('all');
    await expect(chosenOrder(page)).toHaveText('Sitio (ascendente)');
    expect(errors).toEqual([]);
  });
});
