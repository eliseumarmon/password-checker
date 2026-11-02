import { shallowRef } from 'vue';

export interface ConfirmRequest {
  message: string;
  confirmLabel: string;
  danger: boolean;
  resolve: (confirmed: boolean) => void;
}

// One confirmation at a time, shown by the single ConfirmDialog in App.vue.
export const pendingConfirm = shallowRef<ConfirmRequest | null>(null);

export function confirmAction(message: string, confirmLabel: string, danger = false): Promise<boolean> {
  // A request while another is open is refused, leaving the open one untouched.
  if (pendingConfirm.value) return Promise.resolve(false);
  return new Promise(resolve => { pendingConfirm.value = { message, confirmLabel, danger, resolve }; });
}

export function settleConfirm(confirmed: boolean): void {
  const request = pendingConfirm.value;
  pendingConfirm.value = null;
  request?.resolve(confirmed);
}
