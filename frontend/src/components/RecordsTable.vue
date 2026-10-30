<script setup lang="ts">
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TrashIcon from '../TrashIcon.vue';
import { labelReview, labelType } from '../labels';
import type { CredentialSummary } from '../types';

defineProps<{ rows: CredentialSummary[]; busy: boolean }>();
defineEmits<{ edit: [id: string]; trash: [id: string] }>();
</script>

<template>
  <DataTable :value="rows" dataKey="id" sortField="name" :sortOrder="1" stripedRows removableSort class="desktop-table" :paginator="rows.length>30" :rows="30">
    <Column field="name" header="Sitio / App" sortable><template #body="{data:r}"><button class="table-link" @click="$emit('edit', r.id)">{{r.name}}</button><small class="url-truncate">{{r.url}}</small></template></Column>
    <Column field="username" header="Usuario" sortable/>
    <Column field="type" header="Tipo" sortable><template #body="{data:r}">{{labelType(r.type)}}</template></Column>
    <Column field="source" header="Origen" sortable/>
    <Column field="review" header="Revisión" sortable><template #body="{data:r}"><span class="status" :class="r.review">{{labelReview(r.review)}}</span></template></Column>
    <Column header="Acciones"><template #body="{data:r}"><div class="row-actions"><button @click="$emit('edit', r.id)">Editar</button><button class="icon-button danger" aria-label="Mover a la papelera" title="Mover a la papelera" :disabled="busy" @click="$emit('trash', r.id)"><TrashIcon /></button></div></template></Column>
  </DataTable>
  <div class="mobile-cards"><article v-for="r in rows" :key="r.id" class="record-card"><div class="row-between"><strong>{{r.name}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div><p>{{r.username}}</p><p class="muted">{{labelType(r.type)}} · {{r.source}}</p><div class="row-actions"><button @click="$emit('edit', r.id)">Editar →</button><button class="icon-button danger" aria-label="Mover a la papelera" :disabled="busy" @click="$emit('trash', r.id)"><TrashIcon /></button></div></article></div>
</template>
