<script setup lang="ts">
import type { SortDirection } from '../tableState';

// A sortable column header: only the sorted column carries aria-sort (WAI-ARIA APG sortable table).
defineProps<{ label: string; direction: SortDirection | null }>();
defineEmits<{ sort: [] }>();
</script>

<template>
  <th scope="col" class="sortable" :aria-sort="direction ?? undefined">
    <button type="button" class="sort-button" @click="$emit('sort')">{{ label }}<span class="sort-icon" aria-hidden="true">{{ direction === 'ascending' ? '↑' : direction === 'descending' ? '↓' : '↕' }}</span></button>
  </th>
</template>
