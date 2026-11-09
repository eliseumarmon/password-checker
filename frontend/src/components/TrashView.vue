<script setup lang="ts">
import { ref } from 'vue';
import SortHeader from './SortHeader.vue';
import TablePaginator from './TablePaginator.vue';
import { labelOrigin } from '../labels';
import { useRemovalFocus, useTable } from '../tableState';
import type { CredentialSummary } from '../types';

// onRestore is a prop, not an emit, so the table can wait for the action and know when it ends.
const props = defineProps<{ rows: CredentialSummary[]; busy: boolean; onRestore: (id: string) => unknown }>();
const { page, pages, paginated, sorted, visible, sortBy, direction, goTo } = useTable('trash', () => props.rows, { field: 'name', direction: 'ascending' });
const root = ref<HTMLElement>();
const removal = useRemovalFocus(root, sorted, goTo);

function restore(row: CredentialSummary): Promise<void> {
  return removal.run(row, 'restore', () => props.onRestore(row.id));
}
</script>

<template>
  <section class="workspace card">
    <h2>Credenciales descartadas</h2><p>No se exportan. Restaura las que quieras recuperar.</p>
    <p v-if="!rows.length" class="empty">La papelera está vacía.</p>
    <template v-else>
      <div ref="root" class="desktop-table">
        <table aria-label="Credenciales descartadas">
          <thead><tr>
            <SortHeader label="Sitio / App" :direction="direction('name')" @sort="sortBy('name')" />
            <SortHeader label="Usuario" :direction="direction('username')" @sort="sortBy('username')" />
            <SortHeader label="Origen" :direction="direction('source')" @sort="sortBy('source')" />
            <th scope="col">Acciones</th>
          </tr></thead>
          <tbody>
            <tr v-for="r in visible" :key="r.id" :data-row-id="r.id">
              <td><strong>{{r.name}}</strong><small class="url-truncate">{{r.url}}</small></td>
              <td>{{r.username}}</td>
              <td>{{labelOrigin(r.source)}}</td>
              <td><button data-action="restore" :disabled="busy" @click="restore(r)">Restaurar</button></td>
            </tr>
          </tbody>
        </table>
        <TablePaginator v-if="paginated" :page="page" :pages="pages" @go="goTo" />
      </div>
      <div class="mobile-cards"><article v-for="r in rows" :key="r.id" :data-row-id="r.id" class="record-card"><strong>{{r.name}}</strong><p>{{r.username}}</p><p class="muted">{{labelOrigin(r.source)}}</p><button :disabled="busy" @click="onRestore(r.id)">Restaurar</button></article></div>
    </template>
  </section>
</template>
