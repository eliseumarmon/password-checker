<script setup lang="ts">
import { ref } from 'vue';
import type { ConfirmRequest } from '../confirm';
import { useDialogFocus } from '../dialogFocus';

defineProps<{ request: ConfirmRequest }>();
const emit = defineEmits<{ settle: [confirmed: boolean] }>();

const dialog = ref<HTMLElement | null>(null);
const cancelButton = ref<HTMLButtonElement | null>(null);
useDialogFocus(dialog, { initial: () => cancelButton.value, onEscape: () => emit('settle', false) });
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
