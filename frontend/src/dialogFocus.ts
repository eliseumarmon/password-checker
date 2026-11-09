import { nextTick, onMounted, onUnmounted, type Ref } from 'vue';

// Keyboard behavior shared by every modal dialog: where focus starts, Tab staying inside,
// Escape, and where focus goes when the dialog closes.

const FOCUSABLE = 'button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),'
  + 'textarea:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])';

// Open dialogs, topmost last: only the top one reacts to the keyboard.
const openDialogs: object[] = [];

interface Origin {
  opener: HTMLElement | null;
  /** The list holding the row the opener belongs to, and that row's place in it. */
  list: Element | null;
  rowIds: Set<string>;
  rowIndex: number;
  /** Which of the row's buttons opened the dialog. */
  control: number;
  heading: HTMLElement | null;
}

function rowsOf(list: Element): HTMLElement[] {
  return Array.from(list.querySelectorAll<HTMLElement>(':scope > [data-row-id]'));
}

function captureOrigin(): Origin {
  const active = document.activeElement;
  const opener = active instanceof HTMLElement && active !== document.body ? active : null;
  const row = opener?.closest<HTMLElement>('[data-row-id]') ?? null;
  const list = row?.parentElement ?? null;
  const rows = list ? rowsOf(list) : [];
  return {
    opener, list,
    rowIds: new Set(rows.map(item => item.dataset.rowId as string)),
    rowIndex: row ? rows.indexOf(row) : -1,
    control: row && opener ? Array.from(row.querySelectorAll('button')).indexOf(opener as HTMLButtonElement) : -1,
    heading: opener?.closest('section')?.querySelector('h2') ?? null,
  };
}

/** The same control in the next row, or in the closest one left if the row was the last. */
function neighbour({ list, rowIds, rowIndex, control }: Origin): HTMLElement | null {
  if (!list?.isConnected || rowIndex < 0) return null;
  const rows = rowsOf(list);
  if (!rows.length) return null;
  // None of the old rows left means the table moved to another page: its last row is the closest one.
  const samePage = rows.some(row => rowIds.has(row.dataset.rowId as string));
  const row = rows[samePage ? Math.min(rowIndex, rows.length - 1) : rows.length - 1];
  return row.querySelectorAll('button')[control] ?? null;
}

function restoreFocus(origin: Origin): void {
  if (origin.opener?.isConnected) {
    origin.opener.focus();
    return;
  }
  // Only focus that closing the dialog dropped is moved: anywhere else, the person already put it.
  if (document.activeElement && document.activeElement !== document.body) return;
  const control = neighbour(origin);
  if (control) {
    control.focus();
  } else if (origin.heading?.isConnected) {
    origin.heading.tabIndex = -1;
    origin.heading.focus();
  }
}

function keepFocusInside(event: KeyboardEvent, dialog: HTMLElement): void {
  const controls = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(item => item.getClientRects().length);
  if (!controls.length) {
    event.preventDefault();
    return;
  }
  const [first, last] = [controls[0], controls[controls.length - 1]];
  const active = document.activeElement as HTMLElement;
  // Between the edges the browser's own order applies; only the ends wrap around.
  if (!controls.includes(active)) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  } else if (active === (event.shiftKey ? first : last)) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  }
}

export function useDialogFocus(dialog: Ref<HTMLElement | null>, options: { initial: () => HTMLElement | null | undefined; onEscape: () => void }): void {
  const origin = captureOrigin();
  const self = {};

  function onKeydown(event: KeyboardEvent): void {
    if (openDialogs[openDialogs.length - 1] !== self) return;
    if (event.key === 'Escape') options.onEscape();
    else if (event.key === 'Tab' && dialog.value) keepFocusInside(event, dialog.value);
  }

  onMounted(() => {
    openDialogs.push(self);
    document.addEventListener('keydown', onKeydown);
    options.initial()?.focus();
  });

  onUnmounted(async () => {
    document.removeEventListener('keydown', onKeydown);
    openDialogs.splice(openDialogs.indexOf(self), 1);
    // The row that opened the dialog may leave in this same update.
    await nextTick();
    restoreFocus(origin);
  });
}
