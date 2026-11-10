<script setup lang="ts">
import { computed } from 'vue';
import {
  EXTRA_ORDERS, NO_SORT, setTableSort, SORT_COLUMNS, tableSort, UNSORTED_LABEL, type ExtraOrder, type SortDirection, type TableKey,
} from '../tableState';

// Sets the same order as the column headers, and is the only way to sort on a phone, where the
// tables become cards without headers. It also offers orders that no column shows. Each option names
// its direction, so the whole order is read from one control.
const props = defineProps<{ table: TableKey }>();

const UNSORTED = '';
const DIRECTIONS: ExtraOrder['directions'] = [['ascending', 'ascendente'], ['descending', 'descendente']];

const options = computed(() => [
  ...[...SORT_COLUMNS[props.table], ...EXTRA_ORDERS[props.table]].flatMap((order: ExtraOrder) => (
    (order.directions ?? DIRECTIONS).map(([direction, words]) => ({ value: `${order.field}:${direction}`, label: `${order.label} (${words})` }))
  )),
  { value: UNSORTED, label: UNSORTED_LABEL[props.table] },
]);

const chosen = computed({
  get(): string {
    const { field, direction } = tableSort(props.table).value;
    return field ? `${field}:${direction}` : UNSORTED;
  },
  set(value: string): void {
    const [field, direction] = value.split(':') as [string, SortDirection];
    setTableSort(props.table, value === UNSORTED ? NO_SORT : { field, direction });
  },
});
</script>

<template>
  <select v-model="chosen" aria-label="Ordenar">
    <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
  </select>
</template>
