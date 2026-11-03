<script setup lang="ts">
// Shared presentation for the page notices: error and import warning.
// The close button is always outside the scrollable text, so it stays reachable.
defineProps<{ kind: 'error' | 'warning' }>();
defineEmits<{ close: [] }>();
</script>

<template>
  <div :class="kind" :role="kind === 'error' ? 'alert' : 'status'">
    <span v-if="kind === 'error'" class="notice-text"><slot /></span>
    <div v-else class="notice-text"><slot /></div>
    <button type="button" :aria-label="kind === 'error' ? 'Cerrar mensaje de error' : 'Cerrar advertencia de importación'" @click="$emit('close')">×</button>
  </div>
</template>
