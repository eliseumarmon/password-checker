import type { Locator, Page } from '@playwright/test';

// The only place that knows how the desktop tables, their headers and their paginator are built,
// so replacing the table implementation changes this file and not the tests that use it.
// Transitional (native-tables T2): the records table is native while the groups and trash tables still
// use PrimeVue, so each selector accepts both. T3 removes the PrimeVue half.

export type PageControl = 'first' | 'previous' | 'next' | 'last' | number;

const CONTROL_NAMES = { first: 'Primera página', previous: 'Página anterior', next: 'Página siguiente', last: 'Última página' };
const PRIMEVUE_CONTROLS = { first: 'first', previous: 'prev', next: 'next', last: 'last' };

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

export function columnHeader(table: Locator, name: string): Locator {
  return table.locator('thead th', { hasText: name });
}

export async function sortBy(table: Locator, name: string): Promise<void> {
  const header = columnHeader(table, name);
  const button = header.locator('button');
  await (await button.count() ? button : header).click();
}

export function paginator(table: Locator): Locator {
  return table.locator('nav[aria-label="Paginación"], .p-paginator');
}

export function pageControl(table: Locator, control: PageControl): Locator {
  if (typeof control === 'number') {
    return paginator(table).locator(`button[aria-label="Página ${control}"], .p-paginator-page:text-is("${control}")`);
  }
  return paginator(table).locator(`button[aria-label="${CONTROL_NAMES[control]}"], .p-paginator-${PRIMEVUE_CONTROLS[control]}`);
}

export async function goToPage(table: Locator, control: PageControl): Promise<void> {
  await pageControl(table, control).click();
}

/** The number buttons of the paginator, in order. */
export function pageButtons(table: Locator): Locator {
  return paginator(table).locator('button[aria-label^="Página "]:not([aria-label="Página anterior"]):not([aria-label="Página siguiente"]), .p-paginator-page');
}

/** The number button of the page on screen. */
export function currentPage(table: Locator): Locator {
  return paginator(table).locator('[aria-current="page"], .p-paginator-page-selected');
}
