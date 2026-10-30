import type { CredentialDetail, RecordEdit, WorkspaceState } from './types';

/** The server's reason when it sends one as text; validation errors (lists) keep the fallback. */
async function failure(response: Response, fallback: string): Promise<Error> {
  try {
    const { detail } = await response.json() as { detail?: unknown };
    if (typeof detail === 'string' && detail) return new Error(detail);
  } catch { /* Preserve the generic error. */ }
  return new Error(fallback);
}
async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) throw await failure(response, `Error HTTP ${response.status}`);
  return response.json() as Promise<T>;
}
async function downloadFrom(url: string, init: RequestInit, fileName: string, fallback: string): Promise<void> {
  const response = await fetch(url, init);
  if (!response.ok) throw await failure(response, `${fallback} (${response.status})`);
  download(await response.blob(), fileName);
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
  trash: (ids: string[]) => fetch('/api/records/trash', {
    method: 'POST', headers: jsonHeaders, body: JSON.stringify({ ids }),
  }).then(parse<WorkspaceState>),
  mergeExact: () => fetch('/api/merge-exact', { method: 'POST' }).then(parse<WorkspaceState>),
  undo: () => fetch('/api/undo', { method: 'POST' }).then(parse<WorkspaceState>),
  saveSession: (passphrase: string) => downloadFrom('/api/session/save', {
    method: 'POST', headers: jsonHeaders, body: JSON.stringify({ passphrase }),
  }, 'password-checker-session.pwc', 'No se pudo guardar la sesión'),
  loadSession: async (file: File, passphrase: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('passphrase', passphrase);
    return fetch('/api/session/load', { method: 'POST', body: form }).then(parse<WorkspaceState>);
  },
  exportCsv: () => downloadFrom('/api/export', { cache: 'no-store' }, 'bitwarden_import.csv', 'No se pudo exportar'),
};

function download(blob: Blob, fileName: string): void {
    const href = URL.createObjectURL(blob);
    try {
      const anchor = document.createElement('a');
      anchor.href = href; anchor.download = fileName;
      anchor.click();
    } finally { setTimeout(() => URL.revokeObjectURL(href), 1_000); }
}

/** Never navigate to non-web URI or leak credentials through the URL. */
export function safeWebUrl(raw: string): string | null {
  try {
    const url = new URL(raw);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null;
    return url.origin; // No potentially sensitive path/query/hash in outbound navigation.
  } catch { return null; }
}
