import { expect, test, type Page } from '@playwright/test';
import { CHROMIUM_HEADER, chromiumRow, column, desktopTable, seed, showAllRecords } from './tables';

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
