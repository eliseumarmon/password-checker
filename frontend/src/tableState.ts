import { computed, nextTick, ref, toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue';
import { PAGE_SIZE } from './limits';

// Sorting and paging of the desktop tables, without markup (native-tables S4).
// e2e/tables.spec.ts pins this behavior.

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

export type TableKey = 'groups' | 'records' | 'trash';
interface TableMemory { sort: Ref<SortState<string>>; requested: Ref<number> }

// Outlives the components, which unmount when the screen or the tab changes. A reload clears it.
const memory = new Map<TableKey, TableMemory>();

function remembered(key: TableKey, initial: SortState<string>): TableMemory {
  let entry = memory.get(key);
  if (!entry) {
    entry = { sort: ref(initial), requested: ref(1) };
    memory.set(key, entry);
  }
  return entry;
}

/** A new workspace has other rows, so the previous page numbers mean nothing there; the chosen sort stays. */
export function resetTablePages(): void {
  for (const entry of memory.values()) entry.requested.value = 1;
}

export function useTable<T, F extends keyof T & string = keyof T & string>(key: TableKey, rows: MaybeRefOrGetter<readonly T[]>, initial: SortState<NoInfer<F>>) {
  // The page asked for is kept apart from the page shown: while a filter hides the paginator, the page
  // asked for survives and comes back when the filter is cleared.
  const stored = remembered(key, initial);
  const sort = stored.sort as Ref<SortState<F>>;
  const { requested } = stored;
  const sorted = computed(() => sortRows(toValue(rows), sort.value));
  const pages = computed(() => pageCount(sorted.value.length));
  const paginated = computed(() => sorted.value.length > PAGE_SIZE);
  const page = computed(() => Math.min(requested.value, pages.value));
  const visible = computed(() => paginated.value
    ? sorted.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE)
    : sorted.value);
  // With the paginator on screen, fewer pages than the current one move to the last page left.
  // Also on mounting: the rows may have changed while the table was off screen.
  watch(pages, count => { if (paginated.value && requested.value > count) requested.value = count; }, { immediate: true });

  function sortBy(field: F): void {
    sort.value = nextSort(sort.value, field);
    requested.value = 1;
  }
  function direction(field: F): SortDirection | null {
    return sort.value.field === field ? sort.value.direction : null;
  }
  function goTo(target: number): void {
    requested.value = Math.min(Math.max(1, target), pages.value);
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

  /** Runs a row action; the row is remembered only while the action runs, so a cancelled or failed one is forgotten. */
  async function run(row: T, action: string, perform: () => unknown): Promise<void> {
    const heading = root.value?.closest('section')?.querySelector<HTMLElement>('h2') ?? null;
    pending = { id: row.id, action, index: sorted.value.findIndex(item => item.id === row.id), heading };
    try {
      await perform();
    } finally {
      if (pending?.id === row.id) pending = null;
    }
  }

  watch(sorted, async rows => {
    const removal = pending;
    // Other updates while the action runs leave the row in place: keep waiting for it to leave.
    if (!removal || rows.some(row => row.id === removal.id)) return;
    pending = null;
    await nextTick();
    // Only focus that the removal itself dropped is moved. If the row left for another reason (the action
    // was cancelled or failed, and a filter hid the row), focus is wherever the person put it: leave it.
    if (document.activeElement && document.activeElement !== document.body) return;
    const target = rows[removal.index] ?? rows[removal.index - 1];
    // Without a paginator every row is on screen; changing the page would lose the one asked for.
    if (target && rows.length > PAGE_SIZE) goTo(Math.floor(rows.indexOf(target) / PAGE_SIZE) + 1);
    await nextTick();
    const button = target && root.value?.querySelector<HTMLElement>(`tr[data-row-id="${CSS.escape(target.id)}"] [data-action="${removal.action}"]`);
    if (button) return button.focus();
    if (removal.heading) {
      removal.heading.tabIndex = -1;
      removal.heading.focus();
    }
  });

  return { run };
}
