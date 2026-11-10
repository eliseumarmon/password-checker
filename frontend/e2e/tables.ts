import { expect, type Locator, type Page } from '@playwright/test';

// The only place that knows how the desktop tables, their headers and their paginator are built,
// so replacing the table implementation changes this file and not the tests that use it.

export type PageControl = 'first' | 'previous' | 'next' | 'last' | number;

const CONTROL_NAMES = { first: 'Primera página', previous: 'Página anterior', next: 'Página siguiente', last: 'Última página' };

export function desktopTable(page: Page): Locator {
  return page.locator('.desktop-table');
}

export function bodyRows(table: Locator): Locator {
  return table.locator('tbody tr');
}

/** Cells of one column, top to bottom; in the name column, only the name and not the URL below it. */
export function column(table: Locator, index: number): Locator {
  const cells = bodyRows(table).locator(`td:nth-child(${index})`);
  return index === 1 ? cells.locator(':is(.table-link, strong)') : cells;
}

/** The names on the cards that replace the tables on a phone, top to bottom. */
export function cardNames(page: Page): Locator {
  return page.locator('.mobile-cards article strong');
}

export function columnHeader(table: Locator, name: string): Locator {
  return table.locator('thead th', { hasText: name });
}

export async function sortBy(table: Locator, name: string): Promise<void> {
  await columnHeader(table, name).getByRole('button').click();
}

export function paginator(table: Locator): Locator {
  return table.getByRole('navigation', { name: 'Paginación' });
}

export function pageControl(table: Locator, control: PageControl): Locator {
  if (typeof control === 'number') {
    return paginator(table).getByRole('button', { name: `Página ${control}`, exact: true });
  }
  return paginator(table).getByRole('button', { name: CONTROL_NAMES[control], exact: true });
}

export async function goToPage(table: Locator, control: PageControl): Promise<void> {
  await pageControl(table, control).click();
}

/** The number buttons of the paginator, in order. */
export function pageButtons(table: Locator): Locator {
  return paginator(table).getByRole('button', { name: /^Página \d+$/ });
}

/** The number button of the page on screen. */
export function currentPage(table: Locator): Locator {
  return paginator(table).locator('[aria-current="page"]');
}

// Fictional credentials only, built in memory.
export const CHROMIUM_HEADER = 'name,url,username,password,note';

export interface CsvFile { name: string; lines: string[] }

/** Replaces the shared E2E workspace with these files and opens the app.
 * Safe only because the E2E tests run serially against one backend (playwright.config.ts). */
export async function seed(page: Page, files: CsvFile[]): Promise<void> {
  const form = new FormData();
  for (const file of files) form.append('files', new Blob([file.lines.join('\n')], { type: 'text/csv' }), file.name);
  const imported = await page.request.post('/api/import', { multipart: form });
  expect(imported.ok()).toBe(true);
  await page.goto('/');
}

export function chromiumRow(name: string, username: string): string {
  const slug = name.normalize('NFD').replace(/[^\w]+/g, '-').toLowerCase();
  return `${name},https://${slug}.invalid/,${username},fake-${slug}-secret-1234,`;
}

/** `count` sites named "<prefix> 00", "<prefix> 01"… with user names "<prefix>-00"… */
export function numberedRows(prefix: string, count: number): string[] {
  return Array.from({ length: count }, (_, index) => {
    const number = String(index).padStart(2, '0');
    return chromiumRow(`${prefix} ${number}`, `${prefix.toLowerCase()}-${number}`);
  });
}

export async function showAllRecords(page: Page, count: number): Promise<void> {
  await page.getByRole('tab', { name: `Todas (${count})` }).click();
}
