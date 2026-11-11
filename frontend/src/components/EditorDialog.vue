<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import TrashIcon from '../TrashIcon.vue';
import { safeWebUrl } from '../api';
import { confirmAction } from '../confirm';
import { useDialogFocus } from '../dialogFocus';
import { labelOrigin, labelReview } from '../labels';
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
// The 2FA secret has its own visibility, independent of the password's. Its field opts out of
// autofill (new-password plus the 1Password, LastPass and Bitwarden markers): browsers often ignore
// autocomplete="off" on password fields and could overwrite the secret with a saved site password.
const revealedTotp = ref(false);
watch(() => props.record, record => {
  loaded.value = { name: record.name, url: record.url, username: record.username,
    password: record.password, totp: record.totp, note: record.note, review: record.review };
  form.value = { ...loaded.value };
  revealed.value = false;
  revealedTotp.value = false;
}, { immediate: true });
// Edits only reach the server on save, so any other way out of the editor discards them.
const dirty = computed(() => (Object.keys(loaded.value) as (keyof RecordEdit)[]).some(key => form.value[key] !== loaded.value[key]));

// Reloading or closing the tab would also drop the edits: let the browser warn, only while there are some.
// Browsers show their own message, and some mobile ones may not show it at all.
function warnBeforeUnload(event: BeforeUnloadEvent): void {
  event.preventDefault();
  event.returnValue = '';
}
watch(dirty, value => {
  if (value) window.addEventListener('beforeunload', warnBeforeUnload);
  else window.removeEventListener('beforeunload', warnBeforeUnload);
});
onUnmounted(() => window.removeEventListener('beforeunload', warnBeforeUnload));

async function requestClose(): Promise<void> {
  if (dirty.value && !await confirmAction('Hay cambios sin guardar en esta credencial. Si cierras la ficha, se perderán. ¿Continuar?', 'Descartar cambios', true)) return;
  emit('close');
}
const dialog = ref<HTMLElement | null>(null);
const title = ref<HTMLElement | null>(null);
// On a touch screen, focusing a field would raise the on-screen keyboard over half of the record.
const startsOnTitle = window.matchMedia('(pointer: coarse)').matches;
// While a save runs the form still looks dirty: asking to discard it now would leave a confirmation with nothing behind it.
useDialogFocus(dialog, { initial: () => startsOnTitle ? title.value : dialog.value?.querySelector('input'), onEscape: () => { if (!props.busy) void requestClose(); } });
// Trash and restore act on the saved record and close the editor, dropping any unsaved edit.
function confirmDroppingEdits(label: string, danger = false): Promise<boolean> {
  return dirty.value
    ? confirmAction('Hay cambios sin guardar en esta credencial. Si continúas, se perderán. ¿Continuar?', label, danger)
    : Promise.resolve(true);
}
async function requestTrash(): Promise<void> {
  if (await confirmDroppingEdits('Mover a la papelera', true)) emit('trash', props.record.id);
}
async function requestRestore(): Promise<void> {
  if (await confirmDroppingEdits('Restaurar')) emit('restore', props.record.id);
}

async function openSite(url: string): Promise<void> {
  const href = safeWebUrl(url);
  if (!href) return;
  // Check the host, not the whole address: a path must not hide that the address is local.
  if (['localhost', '127.0.0.1'].includes(new URL(href).hostname) && /Android/i.test(navigator.userAgent)) {
    if (!await confirmAction('Esta dirección local apunta a este teléfono, no al ordenador. ¿Abrir de todas formas?', 'Abrir de todas formas')) return;
  }
  window.open(href, '_blank', 'noopener,noreferrer');
}
</script>

<template>
  <div class="overlay modal-overlay" @pointerdown="onBackdropDown" @pointerup="onBackdropUp" @click="onBackdropClick">
    <section ref="dialog" class="editor-dialog card" role="dialog" aria-modal="true" aria-label="Editar credencial">
      <slot />
      <div class="dialog-content">
      <div class="drawer-top"><h2 ref="title" tabindex="-1">Editar credencial</h2><button aria-label="Cerrar" @click="requestClose">✕</button></div>
      <div class="editor-fields editor-grid">
        <label>Nombre<input v-model="form.name" autocomplete="off" /></label>
        <label>URL o paquete Android<input v-model="form.url" autocomplete="off" spellcheck="false" /></label>
        <button v-if="safeWebUrl(form.url || '')" @click="openSite(form.url || '')">↗ Abrir sitio en pestaña nueva</button>
        <p v-else class="muted">Las URI de Android no son enlaces web. Comprueba la app manualmente en el teléfono.</p>
        <label>Usuario<input v-model="form.username" autocomplete="off" /></label>
        <label>Contraseña <span class="secret-input"><input v-model="form.password" :type="revealed?'text':'password'" autocomplete="new-password" spellcheck="false" /><button :aria-label="revealed?'Ocultar contraseña':'Mostrar contraseña'" @click="revealed=!revealed">{{revealed?'Ocultar':'Mostrar'}}</button></span></label>
        <label>Código 2FA (TOTP) <span class="secret-input"><input v-model="form.totp" aria-label="Código 2FA (TOTP)" :type="revealedTotp?'text':'password'" autocomplete="new-password" data-1p-ignore data-lpignore="true" data-bwignore spellcheck="false" /><button :aria-label="revealedTotp?'Ocultar código 2FA':'Mostrar código 2FA'" @click="revealedTotp=!revealedTotp">{{revealedTotp?'Ocultar':'Mostrar'}}</button></span></label>
        <label>Notas<textarea v-model="form.note" rows="5"></textarea></label>
        <label>Estado de revisión<select v-model="form.review"><option value="pending">{{labelReview('pending')}}</option><option value="reviewed">{{labelReview('reviewed')}}</option><option value="incorrect">{{labelReview('incorrect')}}</option></select></label>
        <p class="hint">Editar esta contraseña guardada NO cambia la contraseña real del servicio.</p>
        <p class="muted">Origen inmutable: {{labelOrigin(record.source)}} · línea {{record.line}}</p>
      </div>
      <div class="drawer-actions"><button v-if="record.included" class="danger push-left" :disabled="busy" @click="requestTrash"><TrashIcon /> Descartar</button><button v-else class="push-left" :disabled="busy" @click="requestRestore">Restaurar</button><button @click="requestClose">Cancelar</button><button class="primary" :disabled="busy" @click="$emit('save', form)">Guardar cambios</button></div>
      </div>
    </section>
  </div>
</template>
