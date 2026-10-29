<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { api, safeWebUrl } from './api';
import { useWorkspace } from './store';
import TrashIcon from './TrashIcon.vue';
import type { CredentialDetail, CredentialSummary, DuplicateGroup, FilterType, RecordEdit, Review, Screen } from './types';

const store = useWorkspace();
const screen = ref<Screen>('credentials');
const subtab = ref<'duplicates' | 'all'>('duplicates');
const filterType = ref<FilterType>('all');
const query = ref('');
const pendingOnly = ref(false);
const dragging = ref(false);
const selectedGroup = ref<DuplicateGroup | null>(null);
const selected = ref<CredentialDetail | null>(null);
const form = ref<RecordEdit>({});
const revealed = ref(false);
const note = ref('');
const fileInput = ref<HTMLInputElement | null>(null);
const sessionMode = ref<'save' | 'load' | null>(null);
const sessionPassphrase = ref('');
const sessionConfirmation = ref('');
const sessionFile = ref<File | null>(null);
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
  selectedGroup.value = group; selected.value = null; revealed.value = false;
}
async function openRecord(id: string): Promise<void> {
  try {
    selected.value = await api.detail(id);
    form.value = { name: selected.value.name, url: selected.value.url,
      username: selected.value.username, password: selected.value.password,
      note: selected.value.note, review: selected.value.review };
    revealed.value = false;
  } catch (error) { errorMessage(error); }
}
async function save(): Promise<void> {
  if (!selected.value) return;
  await store.execute(() => api.edit(selected.value!.id, form.value));
  if (!store.error) { selected.value = null; selectedGroup.value = null; }
}
async function quickEdit(id: string, payload: RecordEdit): Promise<void> {
  await store.execute(() => api.edit(id, payload));
  if (!store.error) {
    selectedGroup.value = null;
    if (selected.value?.id === id) selected.value = null;
  }
}
function closeEditor(): void { selected.value = null; revealed.value = false; }
function moveToTrash(id: string): Promise<void> { return quickEdit(id, { included: false }); }
async function trashGroup(group: DuplicateGroup): Promise<void> {
  if (!window.confirm(`Se moverán ${group.count} registros de «${group.name}» a la papelera. Podrás restaurarlos. ¿Continuar?`)) return;
  await store.execute(async () => {
    let state = data.value!;
    for (const member of group.members) state = await api.edit(member.id, { included: false });
    return state;
  });
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
function openSite(url: string): void {
  const href = safeWebUrl(url);
  if (!href) return;
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(href) && /Android/i.test(navigator.userAgent)) {
    if (!window.confirm('Esta dirección local apunta a este teléfono, no al ordenador. ¿Abrir de todas formas?')) return;
  }
  window.open(href, '_blank', 'noopener,noreferrer');
}
function labelReview(review: Review): string {
  return ({ pending: 'Pendiente', reviewed: 'Revisada', verified: 'Verificada', incorrect: 'No funciona' })[review];
}
function labelGroup(kind: DuplicateGroup['kind']): string {
  return ({ exact: 'Copia exacta', conflict: 'Contraseñas diferentes', 'multiple-accounts': 'Varias cuentas' })[kind];
}
function closeSession(): void {
  sessionMode.value = null;
  sessionPassphrase.value = '';
  sessionConfirmation.value = '';
  sessionFile.value = null;
}
function showSession(mode: 'save' | 'load'): void {
  closeSession();
  sessionMode.value = mode;
}
async function submitSession(): Promise<void> {
  store.error = '';
  try {
    if (sessionPassphrase.value.length < 12) {
      throw new Error('Utiliza una contraseña de sesión de al menos 12 caracteres.');
    }
    if (sessionMode.value === 'save') {
      if (sessionPassphrase.value !== sessionConfirmation.value) {
        throw new Error('Las contraseñas de sesión no coinciden.');
      }
      await api.saveSession(sessionPassphrase.value);
    } else if (sessionMode.value === 'load') {
      if (!sessionFile.value) throw new Error('Selecciona el archivo cifrado .pwc.');
      if (data.value?.stats.total && !window.confirm('Abrir otra sesión reemplazará los cambios que estén en memoria. ¿Continuar?')) return;
      await store.execute(() => api.loadSession(sessionFile.value!, sessionPassphrase.value));
      if (store.error) return;
      screen.value = 'credentials';
      subtab.value = 'duplicates';
      selected.value = null; selectedGroup.value = null;
    }
    closeSession();
  } catch (error) { errorMessage(error); }
}


watch(screen, () => { selected.value = null; selectedGroup.value = null; revealed.value = false; });
onMounted(async () => { await store.execute(api.state); });
</script>

<template>
  <div class="shell">
    <aside class="sidebar" :class="{collapsed}" aria-label="Navegación principal">
      <button class="brand" :aria-label="collapsed?'Expandir menú':'Contraer menú'" :title="collapsed?'Expandir menú':'Contraer menú'" :aria-expanded="!collapsed" @click="collapsed=!collapsed"><span class="brand-mark">◇</span><span class="label"><strong>Password Checker</strong><small>Revisión privada de credenciales</small></span></button>
      <nav>
        <button :class="{active:screen==='credentials'}" title="Credenciales" @click="screen='credentials'"><span class="nav-icon">▤</span><span class="label">Credenciales</span></button>
        <button :class="{active:screen==='audit'}" title="Auditoría" @click="screen='audit'"><span class="nav-icon">⬡</span><span class="label">Auditoría</span></button>
        <button :class="{active:screen==='trash'}" :title="`Papelera (${trashed.length})`" @click="screen='trash'"><span class="nav-icon"><TrashIcon /></span><span class="label">Papelera ({{trashed.length}})</span></button>
        <button :class="{active:screen==='settings'}" title="Ajustes" @click="screen='settings'"><span class="nav-icon">⚙</span><span class="label">Ajustes</span></button>
      </nav>
      <p class="sidebar-note label">Solo en este equipo · Sin conexión externa</p>
    </aside>

    <main class="main">
      <div class="sticky-head">
      <header class="topbar">
        <div><h1>{{ ({ credentials: 'Credenciales', audit: 'Auditoría local', trash: 'Papelera', settings: 'Ajustes' })[screen] }}</h1><p>Los originales no se modifican · Las contraseñas permanecen ocultas</p></div>
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
              <Column field="type" header="Tipo" sortable><template #body="{data:g}">{{g.type==='android'?'Android':'Web'}}</template></Column>
              <Column field="count" header="Copias" sortable/>
              <Column field="kind" header="Comparación" sortable><template #body="{data:g}"><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></template></Column>
              <Column header="Acciones"><template #body="{data:g}"><div class="row-actions"><button @click="openGroup(g)">Comparar</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" title="Mover grupo a la papelera" :disabled="store.busy" @click="trashGroup(g)"><TrashIcon /></button></div></template></Column>
            </DataTable>
            <div class="mobile-cards"><article v-for="g in visibleGroups" :key="g.id" class="record-card" @click="openGroup(g)"><div class="row-between"><strong>{{g.name}}</strong><span class="status" :class="g.kind">{{labelGroup(g.kind)}}</span></div><p>{{g.username}}</p><p class="muted">{{g.count}} registros · {{g.type==='android'?'Android':'Web'}}</p><div class="row-actions"><button @click.stop="openGroup(g)">Comparar →</button><button class="icon-button danger" aria-label="Mover grupo a la papelera" :disabled="store.busy" @click.stop="trashGroup(g)"><TrashIcon /></button></div></article></div>
          </template>

          <template v-else>
            <DataTable :value="visibleRows" dataKey="id" sortField="name" :sortOrder="1" stripedRows removableSort class="desktop-table" :paginator="visibleRows.length>30" :rows="30">
              <Column field="name" header="Sitio / App" sortable><template #body="{data:r}"><button class="table-link" @click="openRecord(r.id)">{{r.name}}</button><small class="url-truncate">{{r.url}}</small></template></Column>
              <Column field="username" header="Usuario" sortable/>
              <Column field="type" header="Tipo" sortable><template #body="{data:r}">{{r.type==='android'?'Android':'Web'}}</template></Column>
              <Column field="source" header="Origen" sortable/>
              <Column field="review" header="Revisión" sortable><template #body="{data:r}"><span class="status" :class="r.review">{{labelReview(r.review)}}</span></template></Column>
              <Column header="Acciones"><template #body="{data:r}"><div class="row-actions"><button @click="openRecord(r.id)">Editar</button><button class="icon-button danger" aria-label="Mover a la papelera" title="Mover a la papelera" :disabled="store.busy" @click="moveToTrash(r.id)"><TrashIcon /></button></div></template></Column>
            </DataTable>
            <div class="mobile-cards"><article v-for="r in visibleRows" :key="r.id" class="record-card"><div class="row-between"><strong>{{r.name}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div><p>{{r.username}}</p><p class="muted">{{r.type}} · {{r.source}}</p><div class="row-actions"><button @click="openRecord(r.id)">Editar →</button><button class="icon-button danger" aria-label="Mover a la papelera" :disabled="store.busy" @click="moveToTrash(r.id)"><TrashIcon /></button></div></article></div>
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

    <div v-if="selectedGroup" class="overlay modal-overlay" @click.self="selectedGroup=null">
      <section class="compare-dialog card" role="dialog" aria-modal="true" aria-label="Comparar duplicados">
        <div class="drawer-top"><h2>Comparar registros</h2><button aria-label="Cerrar panel" @click="selectedGroup=null">✕</button></div>
          <p>{{labelGroup(selectedGroup.kind)}} · {{selectedGroup.count}} registros. Ninguna contraseña se elimina por defecto.</p>
          <div class="compare-grid">
            <div v-for="(r,i) in selectedGroup.members" :key="r.id" class="compare-card">
              <div class="row-between"><strong>{{r.source}} · línea {{r.line}}</strong><span class="status" :class="r.review">{{labelReview(r.review)}}</span></div>
              <p>{{r.name}} · {{r.username}}</p><p class="muted" :title="r.url">{{r.url}}</p>
              <div class="compare-flags"><span>URL {{r.match_url?'✓':'≠'}}</span><span>Usuario {{r.match_username?'✓':'≠'}}</span><span>Clave {{r.match_password?'✓':'≠'}}</span></div>
              <div class="compare-actions"><button @click="openRecord(r.id)">Ver / editar</button><button v-if="r.included" class="danger" :disabled="store.busy" @click="moveToTrash(r.id)"><TrashIcon /> Descartar</button></div>
            </div>
          </div>
          <p class="hint">Las coincidencias se comparan respecto al primer registro del grupo. Lo descartado va a la papelera y se puede restaurar.</p>
      </section>
    </div>
    <div v-if="selected" class="overlay modal-overlay" @click.self="closeEditor">
      <section class="editor-dialog card" role="dialog" aria-modal="true" aria-label="Editar credencial">
        <div class="drawer-top"><h2>Editar credencial</h2><button aria-label="Cerrar" @click="closeEditor">✕</button></div>
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
            <p class="muted">Origen inmutable: {{selected.source}} · línea {{selected.line}}</p>
          </div>
          <div class="drawer-actions"><button v-if="selected.included" class="danger push-left" :disabled="store.busy" @click="moveToTrash(selected.id)"><TrashIcon /> Descartar</button><button v-else class="push-left" :disabled="store.busy" @click="restore(selected.id)">Restaurar</button><button @click="closeEditor">Cancelar</button><button class="primary" :disabled="store.busy" @click="save">Guardar cambios</button></div>
      </section>
    </div>
    <div v-if="sessionMode" class="overlay modal-overlay" @click.self="closeSession">
      <section class="session-dialog card" role="dialog" aria-modal="true" aria-label="Sesión cifrada">
        <div class="drawer-top"><h2>{{sessionMode==='save'?'Guardar sesión cifrada':'Abrir sesión anterior'}}</h2><button aria-label="Cerrar" @click="closeSession">✕</button></div>
        <p v-if="sessionMode==='save'">Descarga un archivo cifrado para continuar la revisión otro día, incluso desde otro equipo. No podremos recuperar la contraseña que elijas.</p>
        <p v-else>Selecciona el archivo .pwc y escribe la contraseña con la que lo guardaste.</p>
        <label v-if="sessionMode==='load'" class="session-field">Archivo cifrado
          <input type="file" accept=".pwc" @change="sessionFile=($event.target as HTMLInputElement).files?.[0] || null" />
        </label>
        <label class="session-field">Contraseña de sesión (mínimo 12 caracteres)
          <input v-model="sessionPassphrase" type="password" autocomplete="off" />
        </label>
        <label v-if="sessionMode==='save'" class="session-field">Confirmar contraseña
          <input v-model="sessionConfirmation" type="password" autocomplete="off" />
        </label>
        <p class="hint">La contraseña de sesión nunca se guarda en el navegador ni se envía a Internet.</p>
        <div class="drawer-actions"><button @click="closeSession">Cancelar</button><button class="primary" :disabled="store.busy" @click="submitSession">{{sessionMode==='save'?'Descargar archivo cifrado':'Abrir sesión'}}</button></div>
      </section>
    </div>
    <nav class="mobile-nav" aria-label="Navegación móvil"><button :class="{active:screen==='credentials'}" @click="screen='credentials'">▤<span>Credenciales</span></button><button :class="{active:screen==='audit'}" @click="screen='audit'">⬡<span>Auditoría</span></button><button :class="{active:screen==='trash'}" @click="screen='trash'"><TrashIcon /><span>Papelera</span></button><button :class="{active:screen==='settings'}" @click="screen='settings'">⚙<span>Ajustes</span></button></nav>
  </div>
</template>
