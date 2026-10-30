<script setup lang="ts">
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import type { CredentialSummary } from '../types';

defineProps<{ rows: CredentialSummary[]; busy: boolean }>();
defineEmits<{ restore: [id: string] }>();
</script>

<template>
  <section class="workspace card">
    <h2>Credenciales descartadas</h2><p>No se exportan. Restaura las que quieras recuperar.</p>
    <p v-if="!rows.length" class="empty">La papelera está vacía.</p>
    <template v-else>
      <DataTable :value="rows" dataKey="id" sortField="name" :sortOrder="1" stripedRows removableSort class="desktop-table" :paginator="rows.length>30" :rows="30">
        <Column field="name" header="Sitio / App" sortable><template #body="{data:r}"><strong>{{r.name}}</strong><small class="url-truncate">{{r.url}}</small></template></Column>
        <Column field="username" header="Usuario" sortable/>
        <Column field="source" header="Origen" sortable/>
        <Column header="Acciones"><template #body="{data:r}"><button :disabled="busy" @click="$emit('restore', r.id)">Restaurar</button></template></Column>
      </DataTable>
      <div class="mobile-cards"><article v-for="r in rows" :key="r.id" class="record-card"><strong>{{r.name}}</strong><p>{{r.username}}</p><p class="muted">{{r.source}}</p><button :disabled="busy" @click="$emit('restore', r.id)">Restaurar</button></article></div>
    </template>
  </section>
</template>
