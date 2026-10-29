import type { CredentialDetail, RecordEdit, WorkspaceState } from './types';

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;
    try { const data = await response.json() as { detail?: string }; message = data.detail || message; }
    catch { /* Preserve the generic error. */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
const jsonHeaders = { 'Content-Type': 'application/json' };

export const api = {
  state: () => fetch('/api/workspace', { cache: 'no-store' }).then(parse<WorkspaceState>),
  importFiles: (files: File[]) => {
    const form = new FormData();
    files.forEach(file => form.append('files', file));
    return fetch('/api/import', { method: 'POST', body: form }).then(parse<WorkspaceState>);
  },
  detail: (id: string) => fetch(`/api/records/${encodeURIComponent(id)}`, { cache: 'no-store' }).then(parse<CredentialDetail>),
  edit: (id: string, data: RecordEdit) => fetch(`/api/records/${encodeURIComponent(id)}`, {
    method: 'PATCH', headers: jsonHeaders, body: JSON.stringify(data),
  }).then(parse<WorkspaceState>),
  mergeExact: () => fetch('/api/merge-exact', { method: 'POST' }).then(parse<WorkspaceState>),
  undo: () => fetch('/api/undo', { method: 'POST' }).then(parse<WorkspaceState>),
  exportCsv: async () => {
    const response = await fetch('/api/export', { cache: 'no-store' });
    if (!response.ok) throw new Error(`No se pudo exportar (${response.status})`);
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    try {
      const anchor = document.createElement('a');
      anchor.href = href; anchor.download = 'bitwarden_import.csv';
      anchor.click();
    } finally { setTimeout(() => URL.revokeObjectURL(href), 1_000); }
  },
};

/** Never navigate to non-web URI or leak credentials through the URL. */
export function safeWebUrl(raw: string): string | null {
  try {
    const url = new URL(raw);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null;
    return url.origin; // No potentially sensitive path/query/hash in outbound navigation.
  } catch { return null; }
}
