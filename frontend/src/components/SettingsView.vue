<script setup lang="ts">
defineEmits<{ session: [mode: 'save' | 'load'] }>();
</script>

<template>
  <section class="workspace card"><h2>Ajustes y privacidad</h2><p>Aplicación local, sin telemetría ni fuentes externas.</p><div class="settings-row"><strong>Guardar y reanudar sesión cifrada</strong><span>Archivo local .pwc cifrado con Argon2id + AES-256-GCM</span><div><button @click="$emit('session', 'save')">Guardar</button> <button @click="$emit('session', 'load')">Abrir</button></div></div><div class="settings-row"><strong>Modo móvil con ADB reverse</strong><span>Compatible con loopback, sujeto a configuración de ADB.</span></div><div class="settings-row"><strong>Exportación</strong><span>Formato Bitwarden (CSV) · Confirma antes de descargar.</span></div></section>
</template>
