<script setup lang="ts">
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TrashIcon from '../TrashIcon.vue';
import { labelGroup, labelType } from '../labels';
import type { DuplicateGroup } from '../types';

defineProps<{ groups: DuplicateGroup[]; busy: boolean }>();
defineEmits<{ open: [group: DuplicateGroup]; trash: [group: DuplicateGroup] }>();
</script>

<template>
  <p v-if="!groups.length" class="empty">No hay grupos que coincidan con los filtros.</p>
  <DataTable v-else :value="groups" sortField="name" :sortOrder="1" removableSort stripedRows dataKey="id" class="desktop-table" :paginator="groups.length>30" :rows="30">
    <Column field="name" header="Sitio" sortable><template #body="{data:g}"><button class="table-link" @click="$emit('open', g)">{{g.name}}</button><small class="url-truncate">{{g.url}}</small></template></Column>
    <Column field="username" header="Usuario" sortable/>
    <Column field="type" header="Tipo" sortable><template #body="{data:g}">{{labelType(g.type)}}</template></Column>
    <Column field="count" header="Copias" sortable/>
    <Column field="kind" header="Comparación" sortable><template #body="{data:g}"><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></template></Column>
    <Column header="Acciones"><template #body="{data:g}"><div class="row-actions"><button @click="$emit('open', g)">Comparar</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" title="Mover grupo a la papelera" :disabled="busy" @click="$emit('trash', g)"><TrashIcon /></button></div></template></Column>
  </DataTable>
  <div class="mobile-cards"><article v-for="g in groups" :key="g.id" class="record-card" @click="$emit('open', g)"><div class="row-between"><strong>{{g.name}}</strong><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></div><p>{{g.username}}</p><p class="muted">{{g.count}} registros · {{labelType(g.type)}}</p><div class="row-actions"><button @click.stop="$emit('open', g)">Comparar →</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" :disabled="busy" @click.stop="$emit('trash', g)"><TrashIcon /></button></div></article></div>
</template>
