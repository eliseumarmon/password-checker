import type { Locator, Page } from '@playwright/test';

// The only place that knows how the desktop tables, their headers and their paginator are built,
// so replacing the table implementation changes this file and not the tests that use it.

export type PageControl = 'first' | 'previous' | 'next' | 'last' | number;

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
  await columnHeader(table, name).click();
}

export function paginator(table: Locator): Locator {
  return table.locator('.p-paginator');
}

export function pageControl(table: Locator, control: PageControl): Locator {
  if (typeof control === 'number') {
    return paginator(table).locator('.p-paginator-page', { hasText: new RegExp(`^${control}$`) });
  }
  return paginator(table).locator(`.p-paginator-${control === 'previous' ? 'prev' : control}`);
}

export async function goToPage(table: Locator, control: PageControl): Promise<void> {
  await pageControl(table, control).click();
}

/** The number buttons of the paginator, in order. */
export function pageButtons(table: Locator): Locator {
  return paginator(table).locator('.p-paginator-page');
}

/** The number button of the page on screen. */
export function currentPage(table: Locator): Locator {
  return paginator(table).locator('.p-paginator-page-selected');
}
