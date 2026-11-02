<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import type { ConfirmRequest } from '../confirm';

defineProps<{ request: ConfirmRequest }>();
const emit = defineEmits<{ settle: [confirmed: boolean] }>();

const dialog = ref<HTMLElement | null>(null);
const cancelButton = ref<HTMLButtonElement | null>(null);
// Focus goes back to whatever asked for the confirmation.
const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') emit('settle', false);
  else if (event.key === 'Tab') keepFocusInside(event);
}
// The dialog is modal, so Tab cycles through its own buttons instead of reaching the page behind.
function keepFocusInside(event: KeyboardEvent): void {
  const buttons = Array.from(dialog.value?.querySelectorAll('button') ?? []);
  if (!buttons.length) return;
  event.preventDefault();
  const current = buttons.indexOf(document.activeElement as HTMLButtonElement);
  const next = current === -1 ? 0 : (current + (event.shiftKey ? -1 : 1) + buttons.length) % buttons.length;
  buttons[next].focus();
}
onMounted(() => {
  cancelButton.value?.focus();
  document.addEventListener('keydown', onKeydown);
});
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown);
  opener?.focus();
});
</script>

<template>
  <div class="overlay modal-overlay confirm-overlay" @click.self="$emit('settle', false)">
    <section ref="dialog" class="confirm-dialog card" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-message">
      <h2 id="confirm-title">Confirmar acción</h2>
      <p id="confirm-message">{{request.message}}</p>
      <div class="drawer-actions"><button ref="cancelButton" @click="$emit('settle', false)">Cancelar</button><button :class="request.danger ? 'danger' : 'primary'" @click="$emit('settle', true)">{{request.confirmLabel}}</button></div>
    </section>
  </div>
</template>
