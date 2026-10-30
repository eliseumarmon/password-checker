<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { api } from './api';
import { useWorkspace } from './store';
import TrashIcon from './TrashIcon.vue';
import CompareDialog from './components/CompareDialog.vue';
import EditorDialog from './components/EditorDialog.vue';
import SessionDialog from './components/SessionDialog.vue';
import { SCREENS, labelGroup, labelReview, labelType } from './labels';
import type { CredentialDetail, CredentialSummary, DuplicateGroup, FilterType, RecordEdit, Screen, SessionInput } from './types';

const store = useWorkspace();
const screen = ref<Screen>('credentials');
const subtab = ref<'duplicates' | 'all'>('duplicates');
const filterType = ref<FilterType>('all');
const query = ref('');
const pendingOnly = ref(false);
const dragging = ref(false);
const selectedGroup = ref<DuplicateGroup | null>(null);
const selected = ref<CredentialDetail | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const sessionMode = ref<'save' | 'load' | null>(null);
// Per-viewer convenience only: storage may be unavailable, so failures are ignored.
const SIDEBAR_KEY = 'pc.sidebarCollapsed';
const collapsed = ref(readCollapsed());
function readCollapsed(): boolean {
  try { return localStorage.getItem(SIDEBAR_KEY) === '1'; } catch { return false; }
}
watch(collapsed, value => { try { localStorage.setItem(SIDEBAR_KEY, value ? '1' : '0'); } catch { /* ignore */ } });

const data = computed(() => store.data);
const records = computed(() => data.value?.records ?? []);
const groups = computed(() => data.value?.groups ?? []);
const recById = computed(() => new Map(records.value.map(r => [r.id, r])));
const activeRecords = computed(() => records.value.filter(r => r.included));
const trashed = computed(() => records.value.filter(r => !r.included));
const visibleRows = computed(() => activeRecords.value.filter(r => matches(r)));
const visibleGroups = computed(() => groups.value.filter(g => matches(g) && (!pendingOnly.value || g.pending)));
const progress = computed(() => data.value?.stats.total ? Math.round(100 * data.value.stats.reviewed / data.value.stats.total) : 0);

function matches(row: CredentialSummary | DuplicateGroup): boolean {
  if (filterType.value !== 'all' && row.type !== filterType.value) return false;
  if (pendingOnly.value && 'review' in row && row.review !== 'pending') return false;
  const term = query.value.trim().toLocaleLowerCase();
  return !term || [row.name, row.url, row.username].some(v => v.toLocaleLowerCase().includes(term));
}

function errorMessage(error: unknown): void {
  store.error = error instanceof Error ? error.message : 'No se pudo completar la acción';
}

async function loadFileList(files: FileList | File[]): Promise<void> {
  const selectedFiles = Array.from(files).filter(file => file.name.toLowerCase().endsWith('.csv'));
  if (!selectedFiles.length) { store.error = 'Selecciona archivos CSV'; return; }
  if (data.value?.stats.total && !window.confirm('Importar reemplazará la sesión actual sin guardar. ¿Continuar?')) return;
  await store.execute(() => api.importFiles(selectedFiles));
  selectedGroup.value = null; selected.value = null; subtab.value = 'duplicates'; screen.value = 'credentials';
  if (fileInput.value) fileInput.value.value = '';
}
function onDrop(event: DragEvent): void {
  dragging.value = false;
  if (event.dataTransfer?.files) void loadFileList(event.dataTransfer.files);
}
function openGroup(group: DuplicateGroup): void {
  selectedGroup.value = group; selected.value = null;
}
async function openRecord(id: string): Promise<void> {
  try { selected.value = await api.detail(id); } catch (error) { errorMessage(error); }
}
async function save(form: RecordEdit): Promise<void> {
  if (!selected.value) return;
  await store.execute(() => api.edit(selected.value!.id, form));
  if (!store.error) { selected.value = null; selectedGroup.value = null; }
}
async function quickEdit(id: string, payload: RecordEdit): Promise<void> {
  await store.execute(() => api.edit(id, payload));
  if (!store.error) {
    selectedGroup.value = null;
    if (selected.value?.id === id) selected.value = null;
  }
}
function closeEditor(): void { selected.value = null; }
function moveToTrash(id: string): Promise<void> { return quickEdit(id, { included: false }); }
async function trashGroup(group: DuplicateGroup): Promise<void> {
  if (!window.confirm(`Se moverán ${group.count} registros de «${group.name}» a la papelera. Podrás restaurarlos. ¿Continuar?`)) return;
  await store.execute(() => api.trash(group.members.map(member => member.id)));
  selectedGroup.value = null;
}
function restore(id: string): Promise<void> { return quickEdit(id, { included: true }); }
async function merge(): Promise<void> {
  if (!window.confirm('Las copias idénticas por URL, usuario y contraseña irán a la papelera. Las notas se combinarán. ¿Continuar?')) return;
  await store.execute(api.mergeExact);
  selectedGroup.value = null;
}
async function exportNow(): Promise<void> {
  if (!data.value) return;
  const unresolved = data.value.groups.filter(g => g.kind === 'conflict').length;
  if (!window.confirm(`Se exportarán ${data.value.stats.included} credenciales. ${unresolved} grupos presentan contraseñas conflictivas. Bitwarden no eliminará duplicados automáticamente. ¿Generar CSV?`)) return;
  try { await api.exportCsv(); } catch (error) { errorMessage(error); }
}
function closeSession(): void { sessionMode.value = null; }
function showSession(mode: 'save' | 'load'): void { sessionMode.value = mode; }
async function submitSession({ passphrase, confirmation, file }: SessionInput): Promise<void> {
  store.error = '';
  try {
    if (passphrase.length < 12) {
      throw new Error('Utiliza una contraseña de sesión de al menos 12 caracteres.');
    }
    if (sessionMode.value === 'save') {
      if (passphrase !== confirmation) {
        throw new Error('Las contraseñas de sesión no coinciden.');
      }
      await api.saveSession(passphrase);
    } else if (sessionMode.value === 'load') {
      if (!file) throw new Error('Selecciona el archivo cifrado .pwc.');
      if (data.value?.stats.total && !window.confirm('Abrir otra sesión reemplazará los cambios que estén en memoria. ¿Continuar?')) return;
      await store.execute(() => api.loadSession(file, passphrase));
      if (store.error) return;
      screen.value = 'credentials';
      subtab.value = 'duplicates';
      selected.value = null; selectedGroup.value = null;
    }
    closeSession();
  } catch (error) { errorMessage(error); }
}


watch(screen, () => { selected.value = null; selectedGroup.value = null; });
onMounted(async () => { await store.execute(api.state); });
</script>

<template>
  <div class="shell">
    <aside class="sidebar" :class="{collapsed}" aria-label="Navegación principal">
      <button class="brand" :aria-label="collapsed?'Expandir menú':'Contraer menú'" :title="collapsed?'Expandir menú':'Contraer menú'" :aria-expanded="!collapsed" @click="collapsed=!collapsed"><span class="brand-mark">◇</span><span class="label"><strong>Password Checker</strong><small>Revisión privada de credenciales</small></span></button>
      <nav>
        <button v-for="s in SCREENS" :key="s.id" :class="{active:screen===s.id}" :title="s.id==='trash'?`${s.label} (${trashed.length})`:s.label" @click="screen=s.id"><span class="nav-icon"><TrashIcon v-if="s.id==='trash'" /><template v-else>{{s.icon}}</template></span><span class="label">{{s.label}}<template v-if="s.id==='trash'"> ({{trashed.length}})</template></span></button>
      </nav>
      <p class="sidebar-note label">Solo en este equipo · Sin conexión externa</p>
    </aside>

    <main class="main">
      <div class="sticky-head">
      <header class="topbar">
        <div><h1>{{ SCREENS.find(s => s.id === screen)?.title }}</h1><p>Los originales no se modifican · Las contraseñas permanecen ocultas</p></div>
        <div class="top-actions">
          <button v-if="data?.stats.total" @click="showSession('save')">Guardar sesión cifrada</button>
          <button :disabled="!data?.can_undo || store.busy" @click="store.execute(api.undo)" title="Deshacer último cambio">↶ Deshacer</button>
          <button class="primary" :disabled="!data?.stats.included || store.busy" @click="exportNow">Exportar Bitwarden</button>
        </div>
      </header>
      <div v-if="store.error" class="error" role="alert">{{store.error}} <button @click="store.error=''" aria-label="Cerrar aviso">×</button></div>
      <div v-if="data?.stats.total" class="metrics">
        <div class="metric"><span>Credenciales</span><strong>{{data.stats.total}}</strong></div>
        <div class="metric"><span>Duplicados y conflictos</span><strong>{{data.groups.length}}</strong></div>
        <div class="metric"><span>Revisadas</span><strong>{{data.stats.reviewed}} / {{data.stats.total}}</strong><div class="progress"><span :style="{width:progress+'%'}"></span></div></div>
        <div class="metric"><span>En la papelera</span><strong>{{data.stats.excluded}}</strong></div>
      </div>
      </div>
      <section v-if="!data?.stats.total" class="welcome card">
        <h2>Empieza importando tus contraseñas</h2>
        <p>Arrastra varios CSV de Chrome, Brave y Firefox. Se compararán antes de fusionar nada.</p>
        <div class="dropzone" :class="{dragging}" @dragenter.prevent="dragging=true" @dragover.prevent @dragleave.prevent="dragging=false" @drop.prevent="onDrop">
          <span class="big-icon">⇧</span><strong>Arrastra aquí los CSV</strong>
          <span>o utiliza el selector de archivos</span>
          <button class="primary" :disabled="store.busy" @click="fileInput?.click()">Elegir archivos</button>
          <button @click="showSession('load')">Abrir sesión cifrada anterior</button>
          <input ref="fileInput" type="file" accept=".csv,text/csv" multiple hidden @change="loadFileList(($event.target as HTMLInputElement).files || [])" />
        </div>
        <p class="hint">Los CSV contienen contraseñas en texto plano. No los incluyas en repositorios ni carpetas compartidas.</p>
      </section>

      <template v-else>
        <section v-if="screen==='credentials'" class="workspace card">
          <div class="section-heading"><div><h2>Explorar y consolidar</h2><p>Analiza los registros antes de elegir cuáles exportar.</p></div>
            <div class="heading-actions"><button @click="fileInput?.click()">Importar otros CSV</button><button :disabled="store.busy" @click="merge">Fusionar copias exactas</button></div>
            <input ref="fileInput" hidden type="file" multiple accept=".csv,text/csv" @change="loadFileList(($event.target as HTMLInputElement).files || [])" />
          </div>
          <div class="tabs" role="tablist"><button :class="{selected:subtab==='duplicates'}" @click="subtab='duplicates'">Duplicados ({{groups.length}})</button><button :class="{selected:subtab==='all'}" @click="subtab='all'">Todas ({{activeRecords.length}})</button></div>
          <div class="filters"><input v-model="query" aria-label="Buscar credenciales" placeholder="Buscar por nombre, URL o usuario" /><select v-model="filterType" aria-label="Filtrar tipo"><option value="all">Web y Android</option><option value="web">Solo web</option><option value="android">Solo Android</option></select><label class="check"><input v-model="pendingOnly" type="checkbox" /> Solo pendientes</label></div>

          <template v-if="subtab==='duplicates'">
            <p v-if="!visibleGroups.length" class="empty">No hay grupos que coincidan con los filtros.</p>
            <DataTable v-else :value="visibleGroups" sortField="name" :sortOrder="1" removableSort stripedRows dataKey="id" class="desktop-table" :paginator="visibleGroups.length>30" :rows="30">
              <Column field="name" header="Sitio" sortable><template #body="{data:g}"><button class="table-link" @click="openGroup(g)">{{g.name}}</button><small class="url-truncate">{{g.url}}</small></template></Column>
              <Column field="username" header="Usuario" sortable/>
              <Column field="type" header="Tipo" sortable><template #body="{data:g}">{{labelType(g.type)}}</template></Column>
              <Column field="count" header="Copias" sortable/>
              <Column field="kind" header="Comparación" sortable><template #body="{data:g}"><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></template></Column>
              <Column header="Acciones"><template #body="{data:g}"><div class="row-actions"><button @click="openGroup(g)">Comparar</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" title="Mover grupo a la papelera" :disabled="store.busy" @click="trashGroup(g)"><TrashIcon /></button></div></template></Column>
            </DataTable>
            <div class="mobile-cards"><article v-for="g in visibleGroups" :key="g.id" class="record-card" @click="openGroup(g)"><div class="row-between"><strong>{{g.name}}</strong><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></div><p>{{g.username}}</p><p class="muted">{{g.count}} registros · {{labelType(g.type)}}</p><div class="row-actions"><button @click.stop="openGroup(g)">Comparar →</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" :disabled="store.busy" @click.stop="trashGroup(g)"><TrashIcon /></button></div></article></div>
          </template>

          <template v-else>
            <DataTable :value="visibleRows" dataKey="id" sortField="name" :sortOrder="1" stripedRows removableSort class="desktop-table" :paginator="visibleRows.length>30" :rows="30">
              <Column field="name" header="Sitio / App" sortable><template #body="{data:r}"><button class="table-link" @click="openRecord(r.id)">{{r.name}}</button><small class="url-truncate">{{r.url}}</small></template></Column>
              <Column field="username" header="Usuario" sortable/>
              <Column field="type" header="Tipo" sortable><template #body="{data:r}">{{labelType(r.type)}}</template></Column>
              <Column field="source" header="Origen" sortable/>
              <Column field="review" header="Revisión" sortable><template #body="{data:r}"><span class="status" :class="r.review">{{labelReview(r.review)}}</span></template></Column>
              <Column header="Acciones"><template #body="{data:r}"><div class="row-actions"><button @click="openRecord(r.id)">Editar</button><button class="icon-button danger" aria-label="Mover a la papelera" title="Mover a la papelera" :disabled="store.busy" @click="moveToTrash(r.id)"><TrashIcon /></button></div></template></Column>
            </DataTable>
            <div class="mobile-cards"><article v-for="r in visibleRows" :key="r.id" class="record-card"><div class="row-between"><strong>{{r.name}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div><p>{{r.username}}</p><p class="muted">{{labelType(r.type)}} · {{r.source}}</p><div class="row-actions"><button @click="openRecord(r.id)">Editar →</button><button class="icon-button danger" aria-label="Mover a la papelera" :disabled="store.busy" @click="moveToTrash(r.id)"><TrashIcon /></button></div></article></div>
          </template>
        </section>

        <section v-else-if="screen==='audit'" class="workspace card">
          <h2>Revisión de seguridad offline</h2><p>Las brechas de datos no se consultan. Las advertencias son locales y pueden solaparse.</p>
          <div class="audit-grid"><div class="audit-block"><h3>Contraseñas reutilizadas</h3><p class="audit-count">{{data.audit.reused.length}} grupos</p><details v-for="(ids,i) in data.audit.reused" :key="i"><summary>{{ids.length}} registros comparten contraseña</summary><div v-for="id in ids" :key="id" class="audit-item"><span>{{recById.get(id)?.name}} — {{recById.get(id)?.username}}</span><button @click="openRecord(id)">Revisar</button></div></details><p v-if="!data.audit.reused.length" class="muted">Sin reutilizaciones detectadas.</p></div>
          <div class="audit-block"><h3>Contraseñas poco seguras</h3><p class="audit-count">{{data.audit.weak.length}} credenciales</p><div v-for="id in data.audit.weak" :key="id" class="audit-item"><span>{{recById.get(id)?.name}} — {{recById.get(id)?.username}}</span><button @click="openRecord(id)">Revisar</button></div></div>
          <div class="audit-block"><h3>Datos incompletos</h3><p class="audit-count">{{data.audit.incomplete.length}} credenciales</p><div v-for="id in data.audit.incomplete" :key="id" class="audit-item"><span>{{recById.get(id)?.name}} — {{recById.get(id)?.username}}</span><button @click="openRecord(id)">Revisar</button></div></div>
          <div class="audit-block"><h3>Contraseñas vulneradas</h3><p class="audit-count muted">No comprobadas</p><p>La comprobación de filtraciones requeriría una integración futura.</p></div></div>
        </section>

        <section v-else-if="screen==='trash'" class="workspace card">
          <h2>Credenciales descartadas</h2><p>No se exportan. Restaura las que quieras recuperar.</p>
          <p v-if="!trashed.length" class="empty">La papelera está vacía.</p>
          <template v-else>
            <DataTable :value="trashed" dataKey="id" sortField="name" :sortOrder="1" stripedRows removableSort class="desktop-table" :paginator="trashed.length>30" :rows="30">
              <Column field="name" header="Sitio / App" sortable><template #body="{data:r}"><strong>{{r.name}}</strong><small class="url-truncate">{{r.url}}</small></template></Column>
              <Column field="username" header="Usuario" sortable/>
              <Column field="source" header="Origen" sortable/>
              <Column header="Acciones"><template #body="{data:r}"><button :disabled="store.busy" @click="restore(r.id)">Restaurar</button></template></Column>
            </DataTable>
            <div class="mobile-cards"><article v-for="r in trashed" :key="r.id" class="record-card"><strong>{{r.name}}</strong><p>{{r.username}}</p><p class="muted">{{r.source}}</p><button :disabled="store.busy" @click="restore(r.id)">Restaurar</button></article></div>
          </template>
        </section>

        <section v-else class="workspace card"><h2>Ajustes y privacidad</h2><p>Aplicación local, sin telemetría ni fuentes externas.</p><div class="settings-row"><strong>Guardar y reanudar sesión cifrada</strong><span>Archivo local .pwc cifrado con Argon2id + AES-256-GCM</span><div><button @click="showSession('save')">Guardar</button> <button @click="showSession('load')">Abrir</button></div></div><div class="settings-row"><strong>Modo móvil con ADB reverse</strong><span>Compatible con loopback, sujeto a configuración de ADB.</span></div><div class="settings-row"><strong>Exportación</strong><span>Formato Bitwarden (CSV) · Confirma antes de descargar.</span></div></section>
      </template>
    </main>

    <CompareDialog v-if="selectedGroup" :group="selectedGroup" :busy="store.busy" @close="selectedGroup=null" @edit="openRecord" @trash="moveToTrash" />
    <EditorDialog v-if="selected" :record="selected" :busy="store.busy" @close="closeEditor" @save="save" @trash="moveToTrash" @restore="restore" />
    <SessionDialog v-if="sessionMode" :mode="sessionMode" :busy="store.busy" @close="closeSession" @submit="submitSession" />
    <nav class="mobile-nav" aria-label="Navegación móvil"><button v-for="s in SCREENS" :key="s.id" :class="{active:screen===s.id}" @click="screen=s.id"><TrashIcon v-if="s.id==='trash'" /><template v-else>{{s.icon}}</template><span>{{s.label}}</span></button></nav>
  </div>
</template>
