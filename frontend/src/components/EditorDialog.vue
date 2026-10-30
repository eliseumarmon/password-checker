<script setup lang="ts">
import { ref, watch } from 'vue';
import TrashIcon from '../TrashIcon.vue';
import { safeWebUrl } from '../api';
import type { CredentialDetail, RecordEdit } from '../types';

const props = defineProps<{ record: CredentialDetail; busy: boolean }>();
defineEmits<{ close: []; save: [form: RecordEdit]; trash: [id: string]; restore: [id: string] }>();

const form = ref<RecordEdit>({});
const revealed = ref(false);
watch(() => props.record, record => {
  form.value = { name: record.name, url: record.url, username: record.username,
    password: record.password, note: record.note, review: record.review };
  revealed.value = false;
}, { immediate: true });

function openSite(url: string): void {
  const href = safeWebUrl(url);
  if (!href) return;
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(href) && /Android/i.test(navigator.userAgent)) {
    if (!window.confirm('Esta dirección local apunta a este teléfono, no al ordenador. ¿Abrir de todas formas?')) return;
  }
  window.open(href, '_blank', 'noopener,noreferrer');
}
</script>

<template>
  <div class="overlay modal-overlay" @click.self="$emit('close')">
    <section class="editor-dialog card" role="dialog" aria-modal="true" aria-label="Editar credencial">
      <div class="drawer-top"><h2>Editar credencial</h2><button aria-label="Cerrar" @click="$emit('close')">✕</button></div>
      <div class="editor-fields editor-grid">
        <label>Nombre<input v-model="form.name" autocomplete="off" /></label>
        <label>URL o paquete Android<input v-model="form.url" autocomplete="off" spellcheck="false" /></label>
        <button v-if="safeWebUrl(form.url || '')" @click="openSite(form.url || '')">↗ Abrir sitio en pestaña nueva</button>
        <p v-else class="muted">Las URI de Android no son enlaces web. Comprueba la app manualmente en el teléfono.</p>
        <label>Usuario<input v-model="form.username" autocomplete="off" /></label>
        <label>Contraseña <span class="secret-input"><input v-model="form.password" :type="revealed?'text':'password'" autocomplete="new-password" spellcheck="false" /><button :aria-label="revealed?'Ocultar contraseña':'Mostrar contraseña'" @click="revealed=!revealed">{{revealed?'Ocultar':'Mostrar'}}</button></span></label>
        <label>Notas<textarea v-model="form.note" rows="5"></textarea></label>
        <label>Estado de revisión<select v-model="form.review"><option value="pending">Pendiente</option><option value="reviewed">Revisada (sin verificar acceso)</option><option value="verified">Verificada manualmente</option><option value="incorrect">No funciona</option></select></label>
        <p class="hint">Editar esta contraseña guardada NO cambia la contraseña real del servicio.</p>
        <p class="muted">Origen inmutable: {{record.source}} · línea {{record.line}}</p>
      </div>
      <div class="drawer-actions"><button v-if="record.included" class="danger push-left" :disabled="busy" @click="$emit('trash', record.id)"><TrashIcon /> Descartar</button><button v-else class="push-left" :disabled="busy" @click="$emit('restore', record.id)">Restaurar</button><button @click="$emit('close')">Cancelar</button><button class="primary" :disabled="busy" @click="$emit('save', form)">Guardar cambios</button></div>
    </section>
  </div>
</template>
