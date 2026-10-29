import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from './api';
import type { WorkspaceState } from './types';

export const useWorkspace = defineStore('workspace', () => {
  const data = ref<WorkspaceState | null>(null);
  const busy = ref(false);
  const error = ref('');
  async function execute(action: () => Promise<WorkspaceState>): Promise<void> {
    busy.value = true; error.value = '';
    try { data.value = await action(); }
    catch (e) { error.value = e instanceof Error ? e.message : 'Error inesperado'; }
    finally { busy.value = false; }
  }
  return { data, busy, error, execute };
});
