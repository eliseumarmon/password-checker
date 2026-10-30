<script setup lang="ts">
import type { CredentialSummary } from '../types';

defineProps<{ ids: string[]; records: Map<string, CredentialSummary> }>();
defineEmits<{ review: [id: string] }>();
</script>

<template>
  <div v-for="id in ids" :key="id" class="audit-item"><span>{{records.get(id)?.name}} — {{records.get(id)?.username}}</span><button @click="$emit('review', id)">Revisar</button></div>
</template>
