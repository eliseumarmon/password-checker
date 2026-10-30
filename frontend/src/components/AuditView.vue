<script setup lang="ts">
import AuditItems from './AuditItems.vue';
import type { CredentialSummary, WorkspaceState } from '../types';

defineProps<{ audit: WorkspaceState['audit']; records: Map<string, CredentialSummary> }>();
defineEmits<{ review: [id: string] }>();
</script>

<template>
  <section class="workspace card">
    <h2>Revisión de seguridad offline</h2><p>Las brechas de datos no se consultan. Las advertencias son locales y pueden solaparse.</p>
    <div class="audit-grid">
      <div class="audit-block"><h3>Contraseñas reutilizadas</h3><p class="audit-count">{{audit.reused.length}} grupos</p><details v-for="(ids,i) in audit.reused" :key="i"><summary>{{ids.length}} registros comparten contraseña</summary><AuditItems :ids="ids" :records="records" @review="$emit('review', $event)" /></details><p v-if="!audit.reused.length" class="muted">Sin reutilizaciones detectadas.</p></div>
      <div class="audit-block"><h3>Contraseñas poco seguras</h3><p class="audit-count">{{audit.weak.length}} credenciales</p><AuditItems :ids="audit.weak" :records="records" @review="$emit('review', $event)" /></div>
      <div class="audit-block"><h3>Datos incompletos</h3><p class="audit-count">{{audit.incomplete.length}} credenciales</p><AuditItems :ids="audit.incomplete" :records="records" @review="$emit('review', $event)" /></div>
      <div class="audit-block"><h3>Contraseñas vulneradas</h3><p class="audit-count muted">No comprobadas</p><p>La comprobación de filtraciones requeriría una integración futura.</p></div>
    </div>
  </section>
</template>
