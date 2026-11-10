<script setup lang="ts">
// Shared presentation for the page notices: error, import warning and last change.
// The close button is always outside the scrollable text, so it stays reachable.
defineProps<{ kind: 'error' | 'warning' | 'change'; label?: string }>();
const CLOSE_LABELS = { error: 'Cerrar mensaje de error', warning: 'Cerrar advertencia de importación', change: 'Cerrar aviso de cambio' };
defineEmits<{ close: [] }>();
</script>

<template>
  <div :class="kind" :role="kind === 'error' ? 'alert' : 'status'" :aria-label="label">
    <span v-if="kind === 'error'" class="notice-text"><slot /></span>
    <div v-else class="notice-text"><slot /></div>
    <button type="button" :aria-label="CLOSE_LABELS[kind]" @click="$emit('close')">×</button>
  </div>
</template>
