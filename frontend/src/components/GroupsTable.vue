<script setup lang="ts">
import { ref } from 'vue';
import SortHeader from './SortHeader.vue';
import TablePaginator from './TablePaginator.vue';
import TrashIcon from '../TrashIcon.vue';
import { labelGroup, labelType } from '../labels';
import { useRemovalFocus, useTable } from '../tableState';
import type { DuplicateGroup } from '../types';

// onTrash is a prop, not an emit, so the table can wait for the action and know when it ends.
const props = defineProps<{ groups: DuplicateGroup[]; busy: boolean; onTrash: (group: DuplicateGroup) => unknown }>();
const emit = defineEmits<{ open: [group: DuplicateGroup] }>();
const { page, pages, paginated, sorted, visible, sortBy, direction, goTo } = useTable('groups', () => props.groups, { field: 'name', direction: 'ascending' });
const root = ref<HTMLElement>();
const removal = useRemovalFocus(root, sorted, goTo);

function trash(group: DuplicateGroup): Promise<void> {
  return removal.run(group, 'trash', () => props.onTrash(group));
}
</script>

<template>
  <p v-if="!groups.length" class="empty">No hay grupos que coincidan con los filtros.</p>
  <div v-else ref="root" class="desktop-table">
    <table aria-label="Grupos de duplicados">
      <thead><tr>
        <SortHeader label="Sitio" :direction="direction('name')" @sort="sortBy('name')" />
        <SortHeader label="Usuario" :direction="direction('username')" @sort="sortBy('username')" />
        <SortHeader label="Tipo" :direction="direction('type')" @sort="sortBy('type')" />
        <SortHeader label="Copias" :direction="direction('count')" @sort="sortBy('count')" />
        <SortHeader label="Comparación" :direction="direction('kind')" @sort="sortBy('kind')" />
        <th scope="col">Acciones</th>
      </tr></thead>
      <tbody>
        <tr v-for="g in visible" :key="g.id" :data-row-id="g.id">
          <td><button class="table-link" @click="emit('open', g)">{{g.name}}</button><small class="url-truncate">{{g.url}}</small></td>
          <td>{{g.username}}</td>
          <td>{{labelType(g.type)}}</td>
          <td>{{g.count}}</td>
          <td><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></td>
          <td><div class="row-actions"><button @click="emit('open', g)">Comparar</button><button class="icon-button danger" data-action="trash" aria-label="Mover grupo a la papelera" title="Mover grupo a la papelera" :disabled="busy" @click="trash(g)"><TrashIcon /></button></div></td>
        </tr>
      </tbody>
    </table>
    <TablePaginator v-if="paginated" :page="page" :pages="pages" @go="goTo" />
  </div>
  <div class="mobile-cards"><article v-for="g in groups" :key="g.id" :data-row-id="g.id" class="record-card" @click="$emit('open', g)"><div class="row-between"><strong>{{g.name}}</strong><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></div><p>{{g.username}}</p><p class="muted">{{g.count}} registros · {{labelType(g.type)}}</p><div class="row-actions"><button @click.stop="$emit('open', g)">Comparar →</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" :disabled="busy" @click.stop="onTrash(g)"><TrashIcon /></button></div></article></div>
</template>
