<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { api } from './api';
import { useWorkspace } from './store';
import TrashIcon from './TrashIcon.vue';
import CompareDialog from './components/CompareDialog.vue';
import EditorDialog from './components/EditorDialog.vue';
import SessionDialog from './components/SessionDialog.vue';
import WelcomePanel from './components/WelcomePanel.vue';
import GroupsTable from './components/GroupsTable.vue';
import RecordsTable from './components/RecordsTable.vue';
import AuditView from './components/AuditView.vue';
import TrashView from './components/TrashView.vue';
import SettingsView from './components/SettingsView.vue';
import { SCREENS } from './labels';
import type { CredentialDetail, CredentialSummary, DuplicateGroup, FilterType, RecordEdit, Screen, SessionInput } from './types';

const store = useWorkspace();
const screen = ref<Screen>('credentials');
const subtab = ref<'duplicates' | 'all'>('duplicates');
const filterType = ref<FilterType>('all');
const query = ref('');
const pendingOnly = ref(false);
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
      <input ref="fileInput" type="file" accept=".csv,text/csv" multiple hidden @change="loadFileList(($event.target as HTMLInputElement).files || [])" />
      <WelcomePanel v-if="!data?.stats.total" :busy="store.busy" @pick="fileInput?.click()" @drop="loadFileList" @session="showSession('load')" />

      <template v-else>
        <section v-if="screen==='credentials'" class="workspace card">
          <div class="section-heading"><div><h2>Explorar y consolidar</h2><p>Analiza los registros antes de elegir cuáles exportar.</p></div>
            <div class="heading-actions"><button @click="fileInput?.click()">Importar otros CSV</button><button :disabled="store.busy" @click="merge">Fusionar copias exactas</button></div>
          </div>
          <div class="tabs" role="tablist"><button :class="{selected:subtab==='duplicates'}" @click="subtab='duplicates'">Duplicados ({{groups.length}})</button><button :class="{selected:subtab==='all'}" @click="subtab='all'">Todas ({{activeRecords.length}})</button></div>
          <div class="filters"><input v-model="query" aria-label="Buscar credenciales" placeholder="Buscar por nombre, URL o usuario" /><select v-model="filterType" aria-label="Filtrar tipo"><option value="all">Web y Android</option><option value="web">Solo web</option><option value="android">Solo Android</option></select><label class="check"><input v-model="pendingOnly" type="checkbox" /> Solo pendientes</label></div>
          <GroupsTable v-if="subtab==='duplicates'" :groups="visibleGroups" :busy="store.busy" @open="openGroup" @trash="trashGroup" />
          <RecordsTable v-else :rows="visibleRows" :busy="store.busy" @edit="openRecord" @trash="moveToTrash" />
        </section>
        <AuditView v-else-if="screen==='audit'" :audit="data.audit" :records="recById" @review="openRecord" />
        <TrashView v-else-if="screen==='trash'" :rows="trashed" :busy="store.busy" @restore="restore" />
        <SettingsView v-else @session="showSession" />
      </template>
    </main>

    <CompareDialog v-if="selectedGroup" :group="selectedGroup" :busy="store.busy" @close="selectedGroup=null" @edit="openRecord" @trash="moveToTrash" />
    <EditorDialog v-if="selected" :record="selected" :busy="store.busy" @close="closeEditor" @save="save" @trash="moveToTrash" @restore="restore" />
    <SessionDialog v-if="sessionMode" :mode="sessionMode" :busy="store.busy" @close="closeSession" @submit="submitSession" />
    <nav class="mobile-nav" aria-label="Navegación móvil"><button v-for="s in SCREENS" :key="s.id" :class="{active:screen===s.id}" @click="screen=s.id"><TrashIcon v-if="s.id==='trash'" /><template v-else>{{s.icon}}</template><span>{{s.label}}</span></button></nav>
  </div>
</template>
