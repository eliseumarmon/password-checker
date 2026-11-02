<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import TrashIcon from '../TrashIcon.vue';
import { safeWebUrl } from '../api';
import { confirmAction } from '../confirm';
import { labelReview } from '../labels';
import type { CredentialDetail, RecordEdit } from '../types';

const props = defineProps<{ record: CredentialDetail; busy: boolean }>();
const emit = defineEmits<{ close: []; save: [form: RecordEdit]; trash: [id: string]; restore: [id: string] }>();

// Only a click that starts and ends on the backdrop closes the editor: browsers send a press
// that starts on one side and ends on the other (a text selection, a drag) to the backdrop as a click.
let pressedOnBackdrop = false;
let releasedOnBackdrop = false;
function onBackdropDown(event: PointerEvent): void {
  pressedOnBackdrop = event.target === event.currentTarget;
}
function onBackdropUp(event: PointerEvent): void {
  releasedOnBackdrop = event.target === event.currentTarget;
}
function onBackdropClick(event: MouseEvent): void {
  const close = pressedOnBackdrop && releasedOnBackdrop && event.target === event.currentTarget;
  pressedOnBackdrop = releasedOnBackdrop = false;
  if (close) void requestClose();
}

const form = ref<RecordEdit>({});
const loaded = ref<RecordEdit>({});
const revealed = ref(false);
watch(() => props.record, record => {
  loaded.value = { name: record.name, url: record.url, username: record.username,
    password: record.password, note: record.note, review: record.review };
  form.value = { ...loaded.value };
  revealed.value = false;
}, { immediate: true });
// Edits only reach the server on save, so any other way out of the editor discards them.
const dirty = computed(() => (Object.keys(loaded.value) as (keyof RecordEdit)[]).some(key => form.value[key] !== loaded.value[key]));

async function requestClose(): Promise<void> {
  if (dirty.value && !await confirmAction('Hay cambios sin guardar en esta credencial. Si cierras la ficha, se perderán. ¿Continuar?', 'Descartar cambios', true)) return;
  emit('close');
}

async function openSite(url: string): Promise<void> {
  const href = safeWebUrl(url);
  if (!href) return;
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(href) && /Android/i.test(navigator.userAgent)) {
    if (!await confirmAction('Esta dirección local apunta a este teléfono, no al ordenador. ¿Abrir de todas formas?', 'Abrir de todas formas')) return;
  }
  window.open(href, '_blank', 'noopener,noreferrer');
}
</script>

<template>
  <div class="overlay modal-overlay" @pointerdown="onBackdropDown" @pointerup="onBackdropUp" @click="onBackdropClick">
    <section class="editor-dialog card" role="dialog" aria-modal="true" aria-label="Editar credencial">
      <slot />
      <div class="dialog-content">
      <div class="drawer-top"><h2>Editar credencial</h2><button aria-label="Cerrar" @click="requestClose">✕</button></div>
      <div class="editor-fields editor-grid">
        <label>Nombre<input v-model="form.name" autocomplete="off" /></label>
        <label>URL o paquete Android<input v-model="form.url" autocomplete="off" spellcheck="false" /></label>
        <button v-if="safeWebUrl(form.url || '')" @click="openSite(form.url || '')">↗ Abrir sitio en pestaña nueva</button>
        <p v-else class="muted">Las URI de Android no son enlaces web. Comprueba la app manualmente en el teléfono.</p>
        <label>Usuario<input v-model="form.username" autocomplete="off" /></label>
        <label>Contraseña <span class="secret-input"><input v-model="form.password" :type="revealed?'text':'password'" autocomplete="new-password" spellcheck="false" /><button :aria-label="revealed?'Ocultar contraseña':'Mostrar contraseña'" @click="revealed=!revealed">{{revealed?'Ocultar':'Mostrar'}}</button></span></label>
        <label>Notas<textarea v-model="form.note" rows="5"></textarea></label>
        <label>Estado de revisión<select v-model="form.review"><option value="pending">{{labelReview('pending')}}</option><option value="reviewed">{{labelReview('reviewed')}} (sin verificar acceso)</option><option value="verified">{{labelReview('verified')}} manualmente</option><option value="incorrect">{{labelReview('incorrect')}}</option></select></label>
        <p class="hint">Editar esta contraseña guardada NO cambia la contraseña real del servicio.</p>
        <p class="muted">Origen inmutable: {{record.source}} · línea {{record.line}}</p>
      </div>
      <div class="drawer-actions"><button v-if="record.included" class="danger push-left" :disabled="busy" @click="$emit('trash', record.id)"><TrashIcon /> Descartar</button><button v-else class="push-left" :disabled="busy" @click="$emit('restore', record.id)">Restaurar</button><button @click="requestClose">Cancelar</button><button class="primary" :disabled="busy" @click="$emit('save', form)">Guardar cambios</button></div>
      </div>
    </section>
  </div>
</template>
