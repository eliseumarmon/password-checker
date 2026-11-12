<script setup lang="ts">
import { computed, ref } from 'vue';
import TrashIcon from '../TrashIcon.vue';
import { useDialogFocus } from '../dialogFocus';
import { labelGroup, labelOrigin, labelReview } from '../labels';
import type { CredentialSummary, DuplicateGroup } from '../types';

const props = defineProps<{ group: DuplicateGroup | null; rows: CredentialSummary[]; busy: boolean }>();
const emit = defineEmits<{ close: []; edit: [id: string]; trash: [id: string]; restore: [id: string] }>();

const dialog = ref<HTMLElement | null>(null);
const title = ref<HTMLElement | null>(null);
// Starting on the title lets a screen reader read the comparison before its buttons.
useDialogFocus(dialog, { initial: () => title.value, onEscape: () => emit('close') });

// Matches only exist for members still in the current group; stale ones are not shown.
const matches = computed(() => new Map(props.group?.members.map(member => [member.id, member]) ?? []));
</script>

<template>
  <div class="overlay modal-overlay" @click.self="$emit('close')">
    <section ref="dialog" class="compare-dialog" role="dialog" aria-modal="true" aria-label="Comparar duplicados">
      <slot />
      <div class="dialog-content">
      <div class="drawer-top"><h2 ref="title" tabindex="-1">Comparar registros</h2><button aria-label="Cerrar panel" @click="$emit('close')">✕</button></div>
      <p v-if="group">{{labelGroup(group.kind)}} · {{group.count}} registros. Ninguna contraseña se elimina por defecto.</p>
      <p v-else>Este grupo ya está resuelto.</p>
      <div class="compare-grid">
        <div v-for="r in rows" :key="r.id" class="compare-card">
          <div class="row-between"><strong class="compare-origin">{{labelOrigin(r.source)}}, línea {{r.line}}</strong><span class="status" :class="r.included && r.review">{{r.included ? labelReview(r.review) : 'En la papelera'}}</span></div>
          <dl class="compare-fields"><div><dt>Nombre</dt><dd>{{r.name}}</dd></div><div><dt>Usuario</dt><dd>{{r.username}}</dd></div><div><dt>URL</dt><dd class="compare-url" :title="r.url">{{r.url}}</dd></div></dl>
          <!-- The diff against the group's first active record: a mark and a word for each field. -->
          <ul v-if="matches.get(r.id)" class="compare-flags">
            <li v-for="[label, same] in ([['URL', matches.get(r.id)!.match_url], ['Usuario', matches.get(r.id)!.match_username], ['Contraseña', matches.get(r.id)!.match_password]] as const)" :key="label" :class="same ? 'same' : 'differs'"><span class="mark" aria-hidden="true">{{same ? '=' : '≠'}}</span>{{label}} {{same ? 'igual' : 'distinta'}}</li>
          </ul>
          <div class="compare-actions"><button @click="$emit('edit', r.id)">Ver / editar</button><button v-if="r.included" class="danger" :disabled="busy" @click="$emit('trash', r.id)"><TrashIcon /> Descartar</button><button v-else :disabled="busy" @click="$emit('restore', r.id)">Restaurar</button></div>
        </div>
      </div>
      <p class="hint">Las coincidencias se comparan respecto al primer registro activo del grupo. Lo descartado va a la papelera y se puede restaurar.</p>
      <!-- A toast that floats at the bottom of the list; inside the dialog, so Tab and screen readers reach it. -->
      <slot name="toast" />
      </div>
    </section>
  </div>
</template>
