<script setup lang="ts">
import { ref } from 'vue';
import SortHeader from './SortHeader.vue';
import TablePaginator from './TablePaginator.vue';
import TrashIcon from '../TrashIcon.vue';
import { labelOrigin, labelReview, labelType } from '../labels';
import { SORT_COLUMNS, useRemovalFocus, useTable, type DerivedOrders } from '../tableState';
import type { CredentialSummary } from '../types';

// onTrash is a prop, not an emit, so the table can wait for the action and know when it ends.
// alerts: how many audit lists each record is in (reused, weak, incomplete), by record id.
const props = defineProps<{ rows: CredentialSummary[]; busy: boolean; alerts: ReadonlyMap<string, number>; onTrash: (id: string) => unknown }>();
const emit = defineEmits<{ edit: [id: string] }>();
// The orders the selector offers in «Todas» without a column (review-filters S2).
const derived: DerivedOrders<CredentialSummary> = {
  // More alerts first when descending; ties by name, always A to Z.
  risk: { values: r => [props.alerts.get(r.id) ?? 0], tieBreak: r => r.name },
  // The records of one site stay together: by host, then by the whole URL.
  url: { values: r => [r.host, r.url] },
};
const { page, pages, paginated, sorted, visible, sortBy, direction, goTo } = useTable('records', () => props.rows, derived);
const root = ref<HTMLElement>();
const removal = useRemovalFocus(root, sorted, goTo);

function trash(row: CredentialSummary): Promise<void> {
  return removal.run(row, 'trash', () => props.onTrash(row.id));
}
</script>

<template>
  <div ref="root" class="desktop-table">
    <table aria-label="Credenciales">
      <thead><tr>
        <SortHeader v-for="c in SORT_COLUMNS.records" :key="c.field" :label="c.label" :direction="direction(c.field)" @sort="sortBy(c.field)" />
        <th scope="col">Acciones</th>
      </tr></thead>
      <tbody>
        <tr v-for="r in visible" :key="r.id" :data-row-id="r.id">
          <td><button class="table-link" @click="emit('edit', r.id)">{{r.name}}</button><small class="url-truncate">{{r.url}}</small></td>
          <td>{{r.username}}</td>
          <td>{{labelType(r.type)}}</td>
          <td>{{labelOrigin(r.source)}}</td>
          <td><span class="status" :class="r.review">{{labelReview(r.review)}}</span></td>
          <td><div class="row-actions"><button @click="emit('edit', r.id)">Editar</button><button class="icon-button danger" data-action="trash" aria-label="Mover a la papelera" title="Mover a la papelera" :disabled="busy" @click="trash(r)"><TrashIcon /></button></div></td>
        </tr>
      </tbody>
    </table>
    <TablePaginator v-if="paginated" :page="page" :pages="pages" @go="goTo" />
  </div>
  <div class="mobile-cards"><article v-for="r in sorted" :key="r.id" :data-row-id="r.id" class="record-card"><div class="row-between"><strong>{{r.name}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div><p>{{r.username}}</p><p class="muted">{{labelType(r.type)}} · {{labelOrigin(r.source)}}</p><div class="row-actions"><button @click="$emit('edit', r.id)">Editar →</button><button class="icon-button danger" aria-label="Mover a la papelera" :disabled="busy" @click="onTrash(r.id)"><TrashIcon /></button></div></article></div>
</template>
