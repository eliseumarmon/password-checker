<script setup lang="ts">
// Line icons drawn like TrashIcon: characters such as ⚙ or ⚠ may render as emoji, depending on the font.
export type UiIconName = 'list' | 'shield' | 'tune' | 'sort' | 'sort-up' | 'sort-down' | 'first' | 'previous' | 'next' | 'last' | 'warning';

defineProps<{ name: UiIconName }>();

const PATHS: Record<UiIconName, string> = {
  list: 'M5 6h14M5 12h14M5 18h9',
  shield: 'M12 3.5 18.5 6v5.5c0 4.2-2.8 7.2-6.5 8.8-3.7-1.6-6.5-4.6-6.5-8.8V6z',
  tune: 'M5 8h8M17 8h2M5 16h2M11 16h8M15 6v4M9 14v4',
  sort: 'm8 9 4-4 4 4M8 15l4 4 4-4',
  'sort-up': 'm8 14 4-4 4 4',
  'sort-down': 'm8 10 4 4 4-4',
  first: 'm17 7-5 5 5 5M8 7v10',
  previous: 'm14 7-5 5 5 5',
  next: 'm10 7 5 5-5 5',
  last: 'm7 7 5 5-5 5M16 7v10',
  warning: 'M12 4 21 19H3zM12 10v4M12 16.5v.5',
};
</script>

<template>
  <svg class="icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path :d="PATHS[name]" />
  </svg>
</template>
