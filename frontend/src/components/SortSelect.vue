<script setup lang="ts">
import { computed } from 'vue';
import { setTableSort, SORT_COLUMNS, tableSort, UNSORTED_LABEL, type SortDirection, type TableKey } from '../tableState';

// Sets the same order as the column headers, and is the only way to sort on a phone, where the
// tables become cards without headers. Each option names its direction, so the whole order is read
// from one control.
const props = defineProps<{ table: TableKey }>();

const UNSORTED = '';
const DIRECTIONS: [SortDirection, string][] = [['ascending', 'ascendente'], ['descending', 'descendente']];

const options = computed(() => [
  ...SORT_COLUMNS[props.table].flatMap(column => DIRECTIONS.map(([direction, word]) => (
    { value: `${column.field}:${direction}`, label: `${column.label} (${word})` }
  ))),
  { value: UNSORTED, label: UNSORTED_LABEL[props.table] },
]);

const chosen = computed({
  get(): string {
    const { field, direction } = tableSort(props.table).value;
    return field ? `${field}:${direction}` : UNSORTED;
  },
  set(value: string): void {
    const [field, direction] = value.split(':') as [string, SortDirection];
    setTableSort(props.table, value === UNSORTED ? { field: null, direction: 'ascending' } : { field, direction });
  },
});
</script>

<template>
  <select v-model="chosen" aria-label="Ordenar">
    <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
  </select>
</template>
