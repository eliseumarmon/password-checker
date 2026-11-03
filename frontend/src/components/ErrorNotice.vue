<script setup lang="ts">
import NoticeBase from './NoticeBase.vue';

defineProps<{ message: string }>();
defineEmits<{ close: [] }>();
</script>

<template>
  <NoticeBase kind="error" @close="$emit('close')">{{ message }}</NoticeBase>
</template>
