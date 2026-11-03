<script setup lang="ts">
import { computed, ref } from 'vue';
import NoticeBase from './NoticeBase.vue';
import type { ImportWarning } from '../types';

// Import warnings: file/column names come from an untrusted CSV and are only
// ever rendered as text. From 4 discarded columns on (all files together) the
// list collapses into a summary with an accessible "Ver detalles" toggle.
const props = defineProps<{ warnings: ImportWarning[] }>();
defineEmits<{ close: [] }>();

const expanded = ref(false);
const totalColumns = computed(() => props.warnings.reduce((sum, file) => sum + file.columns.length, 0));
const summarized = computed(() => totalColumns.value >= 4);
function rowsLabel(rows: number): string {
  return `${rows} fila${rows === 1 ? '' : 's'} con datos`;
}
</script>

<template>
  <NoticeBase kind="warning" @close="$emit('close')">
    <p class="warning-title"><span aria-hidden="true">⚠</span> <strong>Importación completada con advertencias</strong></p>
    <p v-if="summarized" class="warning-summary">{{ totalColumns }} columnas descartadas</p>
    <button v-if="summarized" type="button" class="warning-details" :aria-expanded="expanded" @click="expanded = !expanded">Ver detalles</button>
    <ul v-show="!summarized || expanded" class="warning-files">
      <li v-for="(file, fileIndex) in warnings" :key="fileIndex">
        Se han importado {{ file.imported_count }} credenciales de {{ file.file }}
        <ul>
          <li v-for="(column, columnIndex) in file.columns" :key="columnIndex">{{ column.column }}: {{ rowsLabel(column.rows) }}</li>
        </ul>
      </li>
    </ul>
    <p class="warning-footer">Los valores descartados no se incluirán en la exportación.</p>
  </NoticeBase>
</template>
