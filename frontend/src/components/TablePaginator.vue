<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { pageWindow } from '../tableState';

const props = defineProps<{ page: number; pages: number }>();
const emit = defineEmits<{ go: [page: number] }>();
const nav = ref<HTMLElement>();
const numbers = computed(() => pageWindow(props.page, props.pages));

async function go(target: number): Promise<void> {
  emit('go', target);
  await nextTick();
  // A control this move disables (first, previous, next, last) would drop focus to the page: keep it on the current page.
  const active = document.activeElement as HTMLButtonElement | null;
  if (!active || active.disabled || !nav.value?.contains(active)) {
    nav.value?.querySelector<HTMLElement>('[aria-current="page"]')?.focus();
  }
}
</script>

<template>
  <nav ref="nav" class="paginator" aria-label="Paginación">
    <button type="button" aria-label="Primera página" :disabled="page === 1" @click="go(1)">«</button>
    <button type="button" aria-label="Página anterior" :disabled="page === 1" @click="go(page - 1)">‹</button>
    <button v-for="n in numbers" :key="n" type="button" :aria-label="`Página ${n}`" :aria-current="n === page ? 'page' : undefined" @click="go(n)">{{ n }}</button>
    <button type="button" aria-label="Página siguiente" :disabled="page === pages" @click="go(page + 1)">›</button>
    <button type="button" aria-label="Última página" :disabled="page === pages" @click="go(pages)">»</button>
  </nav>
</template>
