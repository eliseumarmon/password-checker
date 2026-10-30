<script setup lang="ts">
import { ref } from 'vue';
import type { SessionInput } from '../types';

defineProps<{ mode: 'save' | 'load'; busy: boolean }>();
defineEmits<{ close: []; submit: [input: SessionInput] }>();

// Secrets live only in this dialog and vanish when it closes.
const passphrase = ref('');
const confirmation = ref('');
const file = ref<File | null>(null);
</script>

<template>
  <div class="overlay modal-overlay" @click.self="$emit('close')">
    <section class="session-dialog card" role="dialog" aria-modal="true" aria-label="Sesión cifrada">
      <div class="drawer-top"><h2>{{mode==='save'?'Guardar sesión cifrada':'Abrir sesión anterior'}}</h2><button aria-label="Cerrar" @click="$emit('close')">✕</button></div>
      <p v-if="mode==='save'">Descarga un archivo cifrado para continuar la revisión otro día, incluso desde otro equipo. No podremos recuperar la contraseña que elijas.</p>
      <p v-else>Selecciona el archivo .pwc y escribe la contraseña con la que lo guardaste.</p>
      <label v-if="mode==='load'" class="session-field">Archivo cifrado
        <input type="file" accept=".pwc" @change="file=($event.target as HTMLInputElement).files?.[0] || null" />
      </label>
      <label class="session-field">Contraseña de sesión (mínimo 12 caracteres)
        <input v-model="passphrase" type="password" autocomplete="off" />
      </label>
      <label v-if="mode==='save'" class="session-field">Confirmar contraseña
        <input v-model="confirmation" type="password" autocomplete="off" />
      </label>
      <p class="hint">La contraseña de sesión nunca se guarda en el navegador ni se envía a Internet.</p>
      <div class="drawer-actions"><button @click="$emit('close')">Cancelar</button><button class="primary" :disabled="busy" @click="$emit('submit', { passphrase, confirmation, file })">{{mode==='save'?'Descargar archivo cifrado':'Abrir sesión'}}</button></div>
    </section>
  </div>
</template>
