import { computed, nextTick, ref, toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue';
import { PAGE_SIZE } from './limits';

// Sorting and paging of the desktop tables, without markup (native-tables S4).
// It reproduces what PrimeVue's DataTable did, as pinned by e2e/tables.spec.ts.

export type SortDirection = 'ascending' | 'descending';
export interface SortState<F extends string> { field: F | null; direction: SortDirection }

const collator = new Intl.Collator(undefined, { numeric: true });
const isEmpty = (value: unknown): boolean => value === null || value === undefined || value === '';

/** Empty values go last in both directions; text follows the browser locale and reads numbers as numbers. */
export function compareValues(a: unknown, b: unknown, direction: SortDirection): number {
  if (isEmpty(a) || isEmpty(b)) return isEmpty(a) === isEmpty(b) ? 0 : isEmpty(a) ? 1 : -1;
  const order = direction === 'ascending' ? 1 : -1;
  if (typeof a === 'string' && typeof b === 'string') return order * collator.compare(a, b);
  const [x, y] = [a as number, b as number];
  return order * (x < y ? -1 : x > y ? 1 : 0);
}

/** A stable sort: tied rows keep their original order in both directions. */
export function sortRows<T, F extends keyof T & string>(rows: readonly T[], sort: SortState<F>): T[] {
  const { field, direction } = sort;
  if (!field) return [...rows];
  return [...rows].sort((a, b) => compareValues(a[field], b[field], direction));
}

/** Each press on a header moves through ascending, descending and back to the original order. */
export function nextSort<F extends string>(sort: SortState<F>, field: F): SortState<F> {
  if (sort.field !== field) return { field, direction: 'ascending' };
  return sort.direction === 'ascending' ? { field, direction: 'descending' } : { field: null, direction: 'ascending' };
}

export function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / PAGE_SIZE));
}

/** Up to five page numbers, centered on the current page whenever possible. */
export function pageWindow(page: number, pages: number, size = 5): number[] {
  const visible = Math.min(size, pages);
  let start = Math.max(0, Math.ceil(page - 1 - visible / 2));
  const end = Math.min(pages - 1, start + visible - 1);
  start = Math.max(0, start - (size - (end - start + 1)));
  return Array.from({ length: end - start + 1 }, (_, index) => start + index + 1);
}

export function useTable<T, F extends keyof T & string = keyof T & string>(rows: MaybeRefOrGetter<readonly T[]>, initial: SortState<NoInfer<F>>) {
  const sort = ref(initial) as Ref<SortState<F>>;
  const page = ref(1);
  const sorted = computed(() => sortRows(toValue(rows), sort.value));
  const pages = computed(() => pageCount(sorted.value.length));
  const paginated = computed(() => sorted.value.length > PAGE_SIZE);
  const visible = computed(() => paginated.value
    ? sorted.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE)
    : sorted.value);
  // When the rows shrink below the current page (a filter, an emptied last page), show the last page left.
  watch(pages, count => { if (page.value > count) page.value = count; });

  function sortBy(field: F): void {
    sort.value = nextSort(sort.value, field);
    page.value = 1;
  }
  function direction(field: F): SortDirection | null {
    return sort.value.field === field ? sort.value.direction : null;
  }
  function goTo(target: number): void {
    page.value = Math.min(Math.max(1, target), pages.value);
  }
  return { sort, page, pages, paginated, sorted, visible, sortBy, direction, goTo };
}

interface PendingRemoval { id: string; action: string; index: number; heading: HTMLElement | null }

/**
 * Keeps keyboard focus when a row action removes its own row (native-tables S3): focus moves to the
 * same action in the next row, or in the previous one if it was the last, or to the section title.
 */
export function useRemovalFocus<T extends { id: string }>(
  root: Ref<HTMLElement | undefined>, sorted: Ref<readonly T[]>, goTo: (page: number) => void,
) {
  let pending: PendingRemoval | null = null;

  function remember(row: T, action: string): void {
    const heading = root.value?.closest('section')?.querySelector<HTMLElement>('h2') ?? null;
    pending = { id: row.id, action, index: sorted.value.findIndex(item => item.id === row.id), heading };
  }

  watch(sorted, async rows => {
    const removal = pending;
    pending = null;
    if (!removal || rows.some(row => row.id === removal.id)) return;
    await nextTick();
    // Only focus that the removal itself dropped is moved. If the row left for another reason (the action
    // was cancelled or failed, and a filter hid the row), focus is wherever the person put it: leave it.
    if (document.activeElement && document.activeElement !== document.body) return;
    const target = rows[removal.index] ?? rows[removal.index - 1];
    if (target) goTo(Math.floor(rows.indexOf(target) / PAGE_SIZE) + 1);
    await nextTick();
    const button = target && root.value?.querySelector<HTMLElement>(`tr[data-row-id="${CSS.escape(target.id)}"] [data-action="${removal.action}"]`);
    if (button) return button.focus();
    if (removal.heading) {
      removal.heading.tabIndex = -1;
      removal.heading.focus();
    }
  });

  return { remember };
}
