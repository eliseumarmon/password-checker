<script setup lang="ts">
defineProps<{ message: string }>();
defineEmits<{ close: [] }>();
</script>

<template>
  <div class="error" role="alert">
    <span>{{ message }}</span>
    <button aria-label="Cerrar aviso" @click="$emit('close')">×</button>
  </div>
</template>
