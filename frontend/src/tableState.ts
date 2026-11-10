import { computed, nextTick, ref, toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue';
import { PAGE_SIZE } from './limits';

// Sorting and paging of the tables, without markup (native-tables S4), with one order per table that
// the column headers and the order selector share (review-filters S2).
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

/**
 * An order that no column shows (review-filters S2): the values it compares in turn, all in the chosen
 * direction, and an optional tie-break that always goes ascending.
 */
export interface DerivedOrder<T> { values: (row: T) => readonly unknown[]; tieBreak?: (row: T) => unknown }
export type DerivedOrders<T> = Readonly<Record<string, DerivedOrder<T>>>;

function compareInTurn(a: readonly unknown[], b: readonly unknown[], direction: SortDirection): number {
  for (let index = 0; index < Math.max(a.length, b.length); index++) {
    const result = compareValues(a[index], b[index], direction);
    if (result) return result;
  }
  return 0;
}

/** A stable sort: tied rows keep their original order in both directions. A derived order wins over a column. */
export function sortRows<T>(rows: readonly T[], sort: SortState<string>, derived: DerivedOrders<T> = {}): T[] {
  const { field, direction } = sort;
  if (!field) return [...rows];
  const order = Object.hasOwn(derived, field) ? derived[field] : undefined;
  if (!order) return [...rows].sort((a, b) => compareValues((a as Record<string, unknown>)[field], (b as Record<string, unknown>)[field], direction));
  // Each row's values are worked out once, not on every comparison.
  const keyed = rows.map(row => ({ row, values: order.values(row), tie: order.tieBreak?.(row) }));
  keyed.sort((a, b) => compareInTurn(a.values, b.values, direction) || compareValues(a.tie, b.tie, 'ascending'));
  return keyed.map(item => item.row);
}

/** No sort: rows keep the order the server sends them in. The headers and the order selector both use it. */
export const NO_SORT: Readonly<SortState<never>> = Object.freeze({ field: null, direction: 'ascending' });

/** Each press on a header moves through ascending, descending and back to the original order. */
export function nextSort<F extends string>(sort: SortState<F>, field: F): SortState<F> {
  if (sort.field !== field) return { field, direction: 'ascending' };
  return sort.direction === 'ascending' ? { field, direction: 'descending' } : NO_SORT;
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

/** A sortable column: the field it sorts by and the label of its header. */
export interface SortColumn { field: string; label: string }

/** The sortable columns of each table, in screen order: the headers and the order selector both read them. */
export const SORT_COLUMNS = {
  records: [
    { field: 'name', label: 'Sitio / App' }, { field: 'username', label: 'Usuario' }, { field: 'type', label: 'Tipo' },
    { field: 'source', label: 'Origen' }, { field: 'review', label: 'Revisión' },
  ],
  groups: [
    { field: 'name', label: 'Sitio' }, { field: 'username', label: 'Usuario' }, { field: 'type', label: 'Tipo' },
    { field: 'count', label: 'Copias' }, { field: 'kind', label: 'Comparación' },
  ],
  trash: [{ field: 'name', label: 'Sitio / App' }, { field: 'username', label: 'Usuario' }, { field: 'source', label: 'Origen' }],
} as const satisfies Record<TableKey, readonly SortColumn[]>;

/** An order only the selector offers, since no column shows it, with the words for each direction it lists. */
export interface ExtraOrder { field: string; label: string; directions?: readonly (readonly [SortDirection, string])[] }

/** The table that lists them must give each one a derived order to `useTable`. */
export const EXTRA_ORDERS: Record<TableKey, readonly ExtraOrder[]> = {
  records: [
    { field: 'risk', label: 'Riesgo', directions: [['descending', 'más alertas primero'], ['ascending', 'menos alertas primero']] },
    { field: 'url', label: 'URL' },
  ],
  groups: [],
  trash: [],
};

/** Unsorted rows keep the order the server sends: records as imported, groups with different passwords first. */
export const UNSORTED_LABEL: Record<TableKey, string> = {
  records: 'Orden de importación', groups: 'Contraseñas diferentes primero', trash: 'Orden de importación',
};

const INITIAL_SORT: SortState<string> = { field: 'name', direction: 'ascending' };
interface TableMemory { sort: Ref<SortState<string>>; requested: Ref<number> }

// Outlives the components, which unmount when the screen or the tab changes. A reload clears it; the
// orders then come back from storage, the pages start again at 1.
const memory = new Map<TableKey, TableMemory>();

// Each table's order also survives a reload (review-filters S3). A per-viewer convenience only: storage may
// be unavailable or hold values this version does not know, so failures are ignored and unknown values dropped.
const STORAGE_PREFIX = 'pc.tableSort.';

function storedSort(key: TableKey): SortState<string> | null {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_PREFIX + key) ?? 'null');
    if (typeof value !== 'object' || value === null) return null;
    const { field, direction } = value as Record<string, unknown>;
    if (direction !== 'ascending' && direction !== 'descending') return null;
    if (field === null) return NO_SORT;
    const fields = [...SORT_COLUMNS[key], ...EXTRA_ORDERS[key]].map(order => order.field);
    return typeof field === 'string' && fields.includes(field) ? { field, direction } : null;
  } catch {
    return null;
  }
}

function storeSort(key: TableKey, { field, direction }: SortState<string>): void {
  try { localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify({ field, direction })); } catch { /* ignore */ }
}

function remembered(key: TableKey): TableMemory {
  let entry = memory.get(key);
  if (!entry) {
    entry = { sort: ref(storedSort(key) ?? { ...INITIAL_SORT }), requested: ref(1) };
    memory.set(key, entry);
  }
  return entry;
}

/** The one order of a table, which its headers and the order selector both show and set. */
export function tableSort(key: TableKey): Readonly<Ref<SortState<string>>> {
  return remembered(key).sort;
}

/** A new order starts again at the first page, wherever it is set from. */
export function setTableSort(key: TableKey, sort: SortState<string>): void {
  const entry = remembered(key);
  entry.sort.value = sort;
  entry.requested.value = 1;
  storeSort(key, sort);
}

/** A new workspace has other rows, so the previous page numbers mean nothing there; the chosen sort stays. */
export function resetTablePages(): void {
  for (const entry of memory.values()) entry.requested.value = 1;
}

export function useTable<T, F extends keyof T & string = keyof T & string>(
  key: TableKey, rows: MaybeRefOrGetter<readonly T[]>, derived: DerivedOrders<T> = {},
) {
  // The page asked for is kept apart from the page shown: while a filter hides the paginator, the page
  // asked for survives and comes back when the filter is cleared.
  const stored = remembered(key);
  const sort = stored.sort as Ref<SortState<F>>;
  const { requested } = stored;
  const sorted = computed(() => sortRows(toValue(rows), sort.value, derived));
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
    setTableSort(key, nextSort(sort.value, field));
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
