import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from './api';
import type { ImportWarning, WorkspaceState } from './types';

export const useWorkspace = defineStore('workspace', () => {
  const data = ref<WorkspaceState | null>(null);
  const busy = ref(false);
  const error = ref('');
  // Import warnings live only in memory, outside the workspace snapshot:
  // never stored in data, the browser or a .pwc session, so a reload starts clean.
  const warnings = ref<ImportWarning[]>([]);
  async function execute(action: () => Promise<WorkspaceState>): Promise<void> {
    busy.value = true; error.value = '';
    try { data.value = await action(); }
    catch (e) { error.value = e instanceof Error ? e.message : 'Error inesperado'; }
    finally { busy.value = false; }
  }
  // A confirmed, successful import replaces the warnings (or clears them when it
  // has none); a pending, cancelled or failed import keeps the previous ones.
  // Kept apart from execute() on purpose: ordinary operations never touch the
  // warnings. Only a session that opens successfully also clears them (App.vue).
  async function importFiles(files: File[]): Promise<void> {
    busy.value = true; error.value = '';
    try {
      const { warnings: reported, ...state } = await api.importFiles(files);
      data.value = state;
      warnings.value = reported;
    }
    catch (e) { error.value = e instanceof Error ? e.message : 'Error inesperado'; }
    finally { busy.value = false; }
  }
  return { data, busy, error, warnings, execute, importFiles };
});
