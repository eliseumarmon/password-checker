<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, watchEffect } from 'vue';
import { api } from './api';
import { useWorkspace } from './store';
import TrashIcon from './TrashIcon.vue';
import ErrorNotice from './components/ErrorNotice.vue';
import WarningNotice from './components/WarningNotice.vue';
import ConfirmDialog from './components/ConfirmDialog.vue';
import CompareDialog from './components/CompareDialog.vue';
import EditorDialog from './components/EditorDialog.vue';
import SessionDialog from './components/SessionDialog.vue';
import WelcomePanel from './components/WelcomePanel.vue';
import GroupsTable from './components/GroupsTable.vue';
import RecordsTable from './components/RecordsTable.vue';
import AuditView from './components/AuditView.vue';
import TrashView from './components/TrashView.vue';
import SettingsView from './components/SettingsView.vue';
import { confirmAction, pendingConfirm, settleConfirm } from './confirm';
import { labelReview, REVIEWS, SCREENS } from './labels';
import { MIN_SESSION_PASSPHRASE_LENGTH } from './limits';
import { resetTablePages } from './tableState';
import type { CredentialDetail, CredentialSummary, DuplicateGroup, FilterReview, FilterType, RecordEdit, Screen, SessionInput, SessionMode } from './types';

const store = useWorkspace();
const screen = ref<Screen>('credentials');
const subtab = ref<'duplicates' | 'all'>('duplicates');
const filterType = ref<FilterType>('all');
const query = ref('');
const filterReview = ref<FilterReview>('all');
// Members fixed when the comparison opens, so it outlives the group when one is discarded.
const compareIds = ref<string[] | null>(null);
const selected = ref<CredentialDetail | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const sessionMode = ref<SessionMode | null>(null);
const stickyHead = ref<HTMLElement | null>(null);
const mobileNav = ref<HTMLElement | null>(null);
const headerHeight = ref(0);
const navHeight = ref(0);
let layoutObserver: ResizeObserver | undefined;
// On the root element, so that the page itself can keep focused controls clear of these bars.
watchEffect(() => {
  const root = document.documentElement.style;
  root.setProperty('--header-height', `${headerHeight.value}px`);
  root.setProperty('--nav-height', `${navHeight.value}px`);
});
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
// A group shows while any of its members is in the chosen state.
const visibleGroups = computed(() => groups.value.filter(g => matches(g)
  && (filterReview.value === 'all' || g.members.some(m => m.review === filterReview.value))));
const compareRows = computed(() => (compareIds.value ?? []).flatMap(id => recById.value.get(id) ?? []));
// Group ids follow their first active member, so the current group is found by membership;
// a group with records from outside the comparison is another group, not this one.
const compareGroup = computed(() => groups.value.find(g => g.members.every(m => compareIds.value?.includes(m.id))) ?? null);
const progress = computed(() => data.value?.stats.total ? Math.round(100 * data.value.stats.reviewed / data.value.stats.total) : 0);
// The error notice lives in the topmost open layer: session > editor > comparison > page.
const errorHost = computed<'session' | 'editor' | 'compare' | 'page' | null>(() => {
  if (!store.error) return null;
  if (sessionMode.value) return 'session';
  if (selected.value) return 'editor';
  if (compareIds.value) return 'compare';
  return 'page';
});

function matches(row: CredentialSummary | DuplicateGroup): boolean {
  if (filterType.value !== 'all' && row.type !== filterType.value) return false;
  if (filterReview.value !== 'all' && 'review' in row && row.review !== filterReview.value) return false;
  const term = query.value.trim().toLocaleLowerCase();
  return !term || [row.name, row.url, row.username].some(v => v.toLocaleLowerCase().includes(term));
}

function errorMessage(error: unknown): void {
  store.error = error instanceof Error ? error.message : 'No se pudo completar la acción';
}

async function loadFileList(files: FileList | File[]): Promise<void> {
  const selectedFiles = Array.from(files).filter(file => file.name.toLowerCase().endsWith('.csv'));
  if (fileInput.value) fileInput.value.value = '';
  if (!selectedFiles.length) { store.error = 'Selecciona archivos CSV'; return; }
  if (data.value?.stats.total && !await confirmAction('Importar reemplazará la sesión actual sin guardar. ¿Continuar?', 'Importar')) return;
  await store.importFiles(selectedFiles);
  resetTablePages();
  compareIds.value = null; selected.value = null; subtab.value = 'duplicates'; screen.value = 'credentials';
}
// Arrows move between the tabs and show each one at once; Tab leaves the group (WAI-ARIA APG tabs).
function onTabKey(event: KeyboardEvent): void {
  // With a modifier the arrows belong to the browser: Alt+Left goes back.
  if ((event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  event.preventDefault();
  subtab.value = subtab.value === 'duplicates' ? 'all' : 'duplicates';
  (event.currentTarget as HTMLElement).querySelector<HTMLElement>(`#tab-${subtab.value}`)?.focus();
}
function openGroup(group: DuplicateGroup): void {
  compareIds.value = group.members.map(member => member.id); selected.value = null;
}
async function openRecord(id: string): Promise<void> {
  try { selected.value = await api.detail(id); } catch (error) { errorMessage(error); }
}
async function save(form: RecordEdit): Promise<void> {
  if (!selected.value) return;
  await store.execute(() => api.edit(selected.value!.id, form));
  if (!store.error) selected.value = null;
}
async function quickEdit(id: string, payload: RecordEdit): Promise<void> {
  await store.execute(() => api.edit(id, payload));
  if (!store.error && selected.value?.id === id) selected.value = null;
}
function closeEditor(): void { selected.value = null; }
function moveToTrash(id: string): Promise<void> { return quickEdit(id, { included: false }); }
async function trashGroup(group: DuplicateGroup): Promise<void> {
  if (!await confirmAction(`Se moverán ${group.count} registros de «${group.name}» a la papelera. Podrás restaurarlos. ¿Continuar?`, 'Mover a la papelera', true)) return;
  await store.execute(() => api.trash(group.members.map(member => member.id)));
  compareIds.value = null;
}
function restore(id: string): Promise<void> { return quickEdit(id, { included: true }); }
async function merge(): Promise<void> {
  if (!await confirmAction('Las copias idénticas por URL, usuario y contraseña irán a la papelera. Las notas se combinarán. ¿Continuar?', 'Fusionar', true)) return;
  await store.execute(api.mergeExact);
  compareIds.value = null;
}
async function exportNow(): Promise<void> {
  if (!data.value) return;
  const unresolved = data.value.groups.filter(g => g.kind === 'conflict').length;
  if (!await confirmAction(`Se exportarán ${data.value.stats.included} credenciales. ${unresolved} grupos presentan contraseñas conflictivas. Bitwarden no eliminará duplicados automáticamente. ¿Generar CSV?`, 'Generar CSV')) return;
  try { await api.exportCsv(); } catch (error) { errorMessage(error); }
}
function closeSession(): void { sessionMode.value = null; }
function showSession(mode: SessionMode): void { sessionMode.value = mode; }
async function submitSession({ passphrase, confirmation, file }: SessionInput): Promise<void> {
  store.error = '';
  try {
    if (passphrase.length < MIN_SESSION_PASSPHRASE_LENGTH) {
      throw new Error(`Utiliza una contraseña de sesión de al menos ${MIN_SESSION_PASSPHRASE_LENGTH} caracteres.`);
    }
    if (sessionMode.value === 'save') {
      if (passphrase !== confirmation) {
        throw new Error('Las contraseñas de sesión no coinciden.');
      }
      await api.saveSession(passphrase);
    } else if (sessionMode.value === 'load') {
      if (!file) throw new Error('Selecciona el archivo cifrado .pwc.');
      if (data.value?.stats.total && !await confirmAction('Abrir otra sesión reemplazará los cambios que estén en memoria. ¿Continuar?', 'Abrir sesión')) return;
      await store.execute(() => api.loadSession(file, passphrase));
      if (store.error) return;
      // Only a session that really opened replaces what the warnings described.
      store.warnings = [];
      resetTablePages();
      screen.value = 'credentials';
      subtab.value = 'duplicates';
      selected.value = null; compareIds.value = null;
    }
    closeSession();
  } catch (error) { errorMessage(error); }
}


watch(screen, () => { selected.value = null; compareIds.value = null; });
onMounted(async () => {
  layoutObserver = new ResizeObserver(() => {
    headerHeight.value = stickyHead.value?.offsetHeight ?? 0;
    navHeight.value = mobileNav.value?.offsetHeight ?? 0;
  });
  if (stickyHead.value) layoutObserver.observe(stickyHead.value);
  if (mobileNav.value) layoutObserver.observe(mobileNav.value);
  await store.execute(api.state);
});
onUnmounted(() => layoutObserver?.disconnect());
</script>

<template>
  <div class="shell">
    <aside class="sidebar" :class="{collapsed}" aria-label="Navegación principal">
      <button class="brand" :aria-label="collapsed?'Expandir menú':'Contraer menú'" :title="collapsed?'Expandir menú':'Contraer menú'" :aria-expanded="!collapsed" @click="collapsed=!collapsed"><span class="brand-mark">◇</span><span class="label"><strong>Password Checker</strong><small>Revisión privada de credenciales</small></span></button>
      <nav>
        <button v-for="s in SCREENS" :key="s.id" :class="{active:screen===s.id}" :aria-current="screen===s.id ? 'page' : undefined" :title="s.showCount?`${s.label} (${trashed.length})`:s.label" @click="screen=s.id"><span class="nav-icon"><TrashIcon v-if="s.icon.kind==='trash'" /><template v-else>{{s.icon.text}}</template></span><span class="label">{{s.label}}<template v-if="s.showCount"> ({{trashed.length}})</template></span></button>
      </nav>
      <p class="sidebar-note label">Solo en este equipo · Sin conexión externa</p>
    </aside>

    <main class="main">
      <div ref="stickyHead" class="sticky-head">
      <header class="topbar">
        <div><h1>{{ SCREENS.find(s => s.id === screen)?.title }}</h1><p>Los originales no se modifican · Las contraseñas permanecen ocultas</p></div>
        <div class="top-actions">
          <button v-if="data?.stats.total" @click="showSession('save')">Guardar sesión cifrada</button>
          <button :disabled="!data?.can_undo || store.busy" @click="store.execute(api.undo)" title="Deshacer último cambio">↶ Deshacer</button>
          <button class="primary" :disabled="!data?.stats.included || store.busy" @click="exportNow">Exportar Bitwarden</button>
        </div>
      </header>
      <div v-if="data?.stats.total" class="metrics">
        <div class="metric"><span>Credenciales</span><strong>{{data.stats.total}}</strong></div>
        <div class="metric"><span>Duplicados y conflictos</span><strong>{{data.groups.length}}</strong></div>
        <div class="metric"><span>Revisadas</span><strong>{{data.stats.reviewed}} / {{data.stats.total}}</strong><div class="progress"><span :style="{width:progress+'%'}"></span></div></div>
        <div class="metric"><span>En la papelera</span><strong>{{data.stats.excluded}}</strong></div>
      </div>
      </div>
      <input ref="fileInput" type="file" accept=".csv,text/csv" multiple hidden @change="loadFileList(($event.target as HTMLInputElement).files || [])" />
      <WelcomePanel v-if="!data?.stats.total" :busy="store.busy" @pick="fileInput?.click()" @files-dropped="loadFileList" @session-requested="showSession" />

      <template v-else>
        <section v-if="screen==='credentials'" class="workspace card">
          <div class="section-heading"><div><h2>Explorar y consolidar</h2><p>Analiza los registros antes de elegir cuáles exportar.</p></div>
            <div class="heading-actions"><button @click="fileInput?.click()">Importar otros CSV</button><button :disabled="store.busy" @click="merge">Fusionar copias exactas</button></div>
          </div>
          <div class="tabs" role="tablist" aria-label="Vista de credenciales" @keydown="onTabKey">
            <button id="tab-duplicates" role="tab" :class="{selected:subtab==='duplicates'}" :aria-selected="subtab==='duplicates'" aria-controls="credentials-panel" :tabindex="subtab==='duplicates' ? 0 : -1" @click="subtab='duplicates'">Duplicados ({{groups.length}})</button>
            <button id="tab-all" role="tab" :class="{selected:subtab==='all'}" :aria-selected="subtab==='all'" aria-controls="credentials-panel" :tabindex="subtab==='all' ? 0 : -1" @click="subtab='all'">Todas ({{activeRecords.length}})</button>
          </div>
          <div id="credentials-panel" role="tabpanel" :aria-labelledby="`tab-${subtab}`">
          <div class="filters"><input v-model="query" aria-label="Buscar credenciales" placeholder="Buscar por nombre, URL o usuario" /><select v-model="filterType" aria-label="Filtrar tipo"><option value="all">Web y Android</option><option value="web">Solo web</option><option value="android">Solo Android</option></select><select v-model="filterReview" aria-label="Filtrar estado"><option value="all">Todos los estados</option><option v-for="review in REVIEWS" :key="review" :value="review">{{labelReview(review)}}</option></select></div>
          <GroupsTable v-if="subtab==='duplicates'" :groups="visibleGroups" :busy="store.busy" @open="openGroup" @trash="trashGroup" />
          <RecordsTable v-else :rows="visibleRows" :busy="store.busy" @edit="openRecord" @trash="moveToTrash" />
          </div>
        </section>
        <AuditView v-else-if="screen==='audit'" :audit="data.audit" :records="recById" @review="openRecord" />
        <TrashView v-else-if="screen==='trash'" :rows="trashed" :busy="store.busy" @restore="restore" />
        <SettingsView v-else @session-requested="showSession" />
      </template>
    </main>

    <CompareDialog v-if="compareIds" :group="compareGroup" :rows="compareRows" :busy="store.busy" @close="compareIds=null" @edit="openRecord" @trash="moveToTrash" @restore="restore">
      <ErrorNotice v-if="errorHost==='compare'" :message="store.error" @close="store.error=''" />
    </CompareDialog>
    <EditorDialog v-if="selected" :record="selected" :busy="store.busy" @close="closeEditor" @save="save" @trash="moveToTrash" @restore="restore">
      <ErrorNotice v-if="errorHost==='editor'" :message="store.error" @close="store.error=''" />
    </EditorDialog>
    <!-- Page-layer notice stack: below every dialog overlay, error on top of the warning. -->
    <div v-if="store.warnings.length || errorHost==='page'" class="page-notices">
      <ErrorNotice v-if="errorHost==='page'" :message="store.error" @close="store.error=''" />
      <WarningNotice v-if="store.warnings.length" :warnings="store.warnings" @close="store.warnings=[]" />
    </div>
    <SessionDialog v-if="sessionMode" :mode="sessionMode" :busy="store.busy" @close="closeSession" @submit="submitSession">
      <ErrorNotice v-if="errorHost==='session'" :message="store.error" @close="store.error=''" />
    </SessionDialog>
    <ConfirmDialog v-if="pendingConfirm" :request="pendingConfirm" @settle="settleConfirm" />
    <nav ref="mobileNav" class="mobile-nav" aria-label="Navegación móvil"><button v-for="s in SCREENS" :key="s.id" :class="{active:screen===s.id}" :aria-current="screen===s.id ? 'page' : undefined" @click="screen=s.id"><TrashIcon v-if="s.icon.kind==='trash'" /><template v-else>{{s.icon.text}}</template><span>{{s.label}}</span></button></nav>
  </div>
</template>
