<script setup lang="ts">
import NoticeBase from './NoticeBase.vue';

// The last change (undo-ux S2): one notice at a time, each replacing the one before.
// Its Deshacer shows while the notice describes a step, and works only while that step is still the last one.
defineProps<{ text: string; showUndo: boolean; canUndo: boolean }>();
defineEmits<{ undo: []; close: [] }>();
</script>

<template>
  <NoticeBase kind="change" label="Último cambio" @close="$emit('close')">
    <span>{{ text }}</span>
    <button v-if="showUndo" type="button" class="notice-action" :disabled="!canUndo" @click="$emit('undo')">Deshacer</button>
  </NoticeBase>
</template>
