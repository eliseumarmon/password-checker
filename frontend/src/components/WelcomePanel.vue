<script setup lang="ts">
import { ref } from 'vue';

defineProps<{ busy: boolean }>();
const emit = defineEmits<{ pick: []; drop: [files: FileList]; session: [] }>();

const dragging = ref(false);
function onDrop(event: DragEvent): void {
  dragging.value = false;
  if (event.dataTransfer?.files) emit('drop', event.dataTransfer.files);
}
</script>

<template>
  <section class="welcome card">
    <h2>Empieza importando tus contraseñas</h2>
    <p>Arrastra varios CSV de Chrome, Brave y Firefox. Se compararán antes de fusionar nada.</p>
    <div class="dropzone" :class="{dragging}" @dragenter.prevent="dragging=true" @dragover.prevent @dragleave.prevent="dragging=false" @drop.prevent="onDrop">
      <span class="big-icon">⇧</span><strong>Arrastra aquí los CSV</strong>
      <span>o utiliza el selector de archivos</span>
      <button class="primary" :disabled="busy" @click="$emit('pick')">Elegir archivos</button>
      <button @click="$emit('session')">Abrir sesión cifrada anterior</button>
    </div>
    <p class="hint">Los CSV contienen contraseñas en texto plano. No los incluyas en repositorios ni carpetas compartidas.</p>
  </section>
</template>
