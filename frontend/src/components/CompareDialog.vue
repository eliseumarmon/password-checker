<script setup lang="ts">
import TrashIcon from '../TrashIcon.vue';
import { labelGroup, labelReview } from '../labels';
import type { DuplicateGroup } from '../types';

defineProps<{ group: DuplicateGroup; busy: boolean }>();
defineEmits<{ close: []; edit: [id: string]; trash: [id: string] }>();
</script>

<template>
  <div class="overlay modal-overlay" @click.self="$emit('close')">
    <section class="compare-dialog card" role="dialog" aria-modal="true" aria-label="Comparar duplicados">
      <div class="drawer-top"><h2>Comparar registros</h2><button aria-label="Cerrar panel" @click="$emit('close')">✕</button></div>
      <p>{{labelGroup(group.kind)}} · {{group.count}} registros. Ninguna contraseña se elimina por defecto.</p>
      <div class="compare-grid">
        <div v-for="r in group.members" :key="r.id" class="compare-card">
          <div class="row-between"><strong>{{r.source}} · línea {{r.line}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div>
          <p>{{r.name}} · {{r.username}}</p><p class="muted" :title="r.url">{{r.url}}</p>
          <div class="compare-flags"><span>URL {{r.match_url?'✓':'≠'}}</span><span>Usuario {{r.match_username?'✓':'≠'}}</span><span>Clave {{r.match_password?'✓':'≠'}}</span></div>
          <div class="compare-actions"><button @click="$emit('edit', r.id)">Ver / editar</button><button v-if="r.included" class="danger" :disabled="busy" @click="$emit('trash', r.id)"><TrashIcon /> Descartar</button></div>
        </div>
      </div>
      <p class="hint">Las coincidencias se comparan respecto al primer registro del grupo. Lo descartado va a la papelera y se puede restaurar.</p>
    </section>
  </div>
</template>
